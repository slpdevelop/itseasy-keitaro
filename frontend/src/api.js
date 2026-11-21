const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
  });
  const raw = await response.text();
  let data = null;
  try { data = raw ? JSON.parse(raw) : null; } catch { data = raw; }
  if (!response.ok) {
    const detail = data?.detail || data?.message || (typeof data === 'string' ? data : response.statusText);
    throw new Error(`${response.status}: ${detail}`);
  }
  return data;
}

export const api = {
  campaigns: () => request('/campaigns'),
  campaign: (id) => request(`/campaigns/${id}`),
  keitaroOffers: () => request('/offers'),
  localOffers: () => request('/offers/local'),
  createCampaign: (payload) => request('/campaigns', { method: 'POST', body: JSON.stringify(payload) }),
  syncFromKeitaro: () => request('/offers/sync/from-keitaro', { method: 'POST' }),
  syncToKeitaro: () => request('/offers/sync/to-keitaro', { method: 'POST' }),
  syncCampaign: (campaignId) => request(`/campaigns/${campaignId}/sync`, { method: 'POST' }),
  updateFlow: (flowId, offers) => request(`/campaigns/streams/${flowId}`, {
    method: 'PUT', body: JSON.stringify({ offers }),
  }),
};

export function normalizeList(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  if (Array.isArray(value?.data)) return value.data;
  return [];
}
export function getId(item) { return item?.id ?? item?.campaign_id ?? item?.keitaro_id ?? item?.uuid; }
export function getName(item) { return item?.name ?? item?.campaign_name ?? item?.title ?? `Company ${getId(item) ?? ''}`; }
export function getGeo(item) {
  const geoFlow = item?.flows?.find(flow => String(flow?.type ?? '').toLowerCase() === 'geo');
  return item?.geo ?? item?.geo_code ?? item?.country ?? item?.country_code ?? geoFlow?.country ?? '—';
}
export function getKeitaroId(item) { return item?.keitaro_id ?? item?.campaign_id ?? item?.id ?? item?.uuid; }
export function getFlows(detail) { return detail?.flows ?? detail?.streams ?? detail?.campaign?.flows ?? detail?.campaign?.streams ?? []; }
export function getFlowOffers(flow) { return flow?.offers ?? flow?.offer_bindings ?? flow?.landings ?? []; }
export function getOfferId(offer) { return offer?.offer_id ?? offer?.keitaro_id ?? offer?.id; }
export function getOfferName(offer) { return offer?.name ?? offer?.title ?? offer?.offer_name ?? `Offer ${getOfferId(offer) ?? ''}`; }