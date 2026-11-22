"""Domain rules for local flow-offer configuration."""

from app.models.models import Flow, FlowOffer, FlowOfferState, FlowType, Offer
from app.schemas.flow import FlowOfferUpdate


class FlowOfferRuleError(ValueError):
    """A flow-offer configuration violates a domain invariant."""


def apply_offer_updates(
    flow: Flow,
    items: list[FlowOfferUpdate],
    offers_by_keitaro_id: dict[int, Offer],
) -> None:
    """Apply a full replacement and normalize 100% across active offers only.

    DISABLED offers remain attached for later re-enabling but carry zero share.
    """
    if flow.type != FlowType.OFFER:
        raise FlowOfferRuleError("Offers can only be changed on OFFER flows")

    by_offer_id = {link.offer_id: link for link in flow.offers}
    before = {
        link.offer.id: (link.share, link.state, link.deleted)
        for link in flow.offers
    }
    incoming_ids = set()

    for item in items:
        offer = offers_by_keitaro_id[item.offer_id]
        incoming_ids.add(offer.id)
        link = by_offer_id.get(offer.id)
        if link is None:
            link = FlowOffer(offer=offer, share=0)
            flow.offers.append(link)
            by_offer_id[offer.id] = link
        else:
            link.offer = offer

        state = item.state
        deleted = item.deleted or state == "deleted"
        if state == "deleted":
            state = (link.state or FlowOfferState.ACTIVE).value
        if state not in {FlowOfferState.ACTIVE.value, FlowOfferState.DISABLED.value}:
            raise FlowOfferRuleError(f"Invalid offer state: {state}")
        link.state = FlowOfferState(state)
        link.deleted = deleted
        link.share = 0 if deleted else item.share
        link.pinned = False if deleted else item.pinned

    for link in flow.offers:
        if link.offer.id not in incoming_ids:
            link.deleted = True
            link.share = 0
            link.pinned = False

    active = [
        link for link in flow.offers
        if not link.deleted and link.state == FlowOfferState.ACTIVE
    ]
    pinned = [link for link in active if link.pinned]
    unpinned = [link for link in active if not link.pinned]
    pinned_total = sum(link.share for link in pinned)
    if pinned_total > 100:
        raise FlowOfferRuleError("The total share of pinned active offers cannot exceed 100%")
    remaining = 100 - pinned_total
    if not unpinned and active and remaining != 0:
        raise FlowOfferRuleError("All active offers are pinned; their shares must total exactly 100%")
    if unpinned:
        base, remainder = divmod(remaining, len(unpinned))
        remainder_start = len(unpinned) - remainder
        for index, link in enumerate(unpinned):
            link.share = base + (1 if index >= remainder_start else 0)

    for link in flow.offers:
        if link.deleted or link.state == FlowOfferState.DISABLED:
            link.share = 0
        previous = before.get(link.offer.id)
        if previous is None or previous != (link.share, link.state, link.deleted):
            link.synced = False
            flow.synced = False
