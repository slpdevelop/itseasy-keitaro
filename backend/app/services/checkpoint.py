"""PostgreSQL-backed idempotency checkpoints for campaign creation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import OperationInProgressError
from app.models.models import CampaignCreationOperation

logger = logging.getLogger(__name__)


class Checkpoint:
    """Persist each completed orchestration step in PostgreSQL.

    A unique operation key prevents concurrent duplicate requests. Failed requests
    can resume; stale leases are recoverable after one hour. Completed keys are
    retained for 24 hours to make client retries idempotent.
    """

    LEASE_TTL = timedelta(hours=1)
    RESULT_TTL = timedelta(hours=24)

    def __init__(
        self,
        key: str,
        request_hash: str,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.key = key
        self.request_hash = request_hash
        self.session_factory = session_factory
        self.owner_token = str(uuid4())

    async def acquire(self) -> bool:
        """Claim an operation; return False when its completed result is reusable."""
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session, session.begin():
            await session.execute(
                delete(CampaignCreationOperation).where(
                    (
                        (CampaignCreationOperation.status == "completed")
                        & (CampaignCreationOperation.updated_at < now - self.RESULT_TTL)
                    )
                    | (
                        (CampaignCreationOperation.status == "failed")
                        & (CampaignCreationOperation.updated_at < now - timedelta(days=7))
                    )
                )
            )
            await session.execute(
                insert(CampaignCreationOperation)
                .values(
                    key=self.key,
                    request_hash=self.request_hash,
                    owner_token=self.owner_token,
                    status="running",
                    steps={},
                    created_at=now,
                    updated_at=now,
                )
                .on_conflict_do_nothing(index_elements=[CampaignCreationOperation.key])
            )
            operation = await session.scalar(
                select(CampaignCreationOperation)
                .where(CampaignCreationOperation.key == self.key)
                .with_for_update()
            )
            assert operation is not None

            if operation.owner_token == self.owner_token:
                return True

            age = now - operation.updated_at
            if operation.request_hash != self.request_hash:
                if operation.status == "running" and age < self.LEASE_TTL:
                    raise OperationInProgressError(
                        "A campaign with this name is being created with different parameters"
                    )
                if operation.status == "failed" or (
                    operation.status == "running" and age >= self.LEASE_TTL
                ):
                    raise OperationInProgressError(
                        "A previous incomplete campaign creation uses this name; retry its original request first"
                    )
            elif operation.status == "completed" and age < self.RESULT_TTL:
                return False
            elif operation.status == "running" and age < self.LEASE_TTL:
                raise OperationInProgressError()

            was_completed = operation.status == "completed"
            operation.request_hash = self.request_hash
            operation.owner_token = self.owner_token
            operation.status = "running"
            if was_completed:
                operation.steps = {}
            operation.updated_at = now
            return True

    async def run(self, step: str, fn: Callable[[], Awaitable[Any]]) -> Any:
        """Return a persisted step result or execute and persist the step."""
        async with self.session_factory() as session:
            operation = await session.get(CampaignCreationOperation, self.key)
            if operation is None or operation.owner_token != self.owner_token:
                raise OperationInProgressError()
            if step in operation.steps:
                return operation.steps[step]

        try:
            result = await fn()
        except Exception:
            logger.exception("Campaign creation step %s failed", step)
            raise

        async with self.session_factory() as session, session.begin():
            operation = await session.scalar(
                select(CampaignCreationOperation)
                .where(
                    CampaignCreationOperation.key == self.key,
                    CampaignCreationOperation.owner_token == self.owner_token,
                )
                .with_for_update()
            )
            if operation is None:
                raise OperationInProgressError()
            operation.steps = {**operation.steps, step: result}
            operation.updated_at = datetime.now(timezone.utc)
        return result

    async def get_step(self, step: str) -> Any:
        async with self.session_factory() as session:
            operation = await session.get(CampaignCreationOperation, self.key)
            return operation.steps.get(step) if operation else None

    async def complete(self) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(CampaignCreationOperation)
                .where(
                    CampaignCreationOperation.key == self.key,
                    CampaignCreationOperation.owner_token == self.owner_token,
                )
                .values(status="completed", updated_at=datetime.now(timezone.utc))
            )

    async def fail(self) -> None:
        async with self.session_factory() as session, session.begin():
            await session.execute(
                update(CampaignCreationOperation)
                .where(
                    CampaignCreationOperation.key == self.key,
                    CampaignCreationOperation.owner_token == self.owner_token,
                )
                .values(status="failed", updated_at=datetime.now(timezone.utc))
            )
