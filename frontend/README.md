# Keitaro Companies UI

React + Vite frontend for the FastAPI / Keitaro integration.

## Run locally

```bash
npm install
cp .env.example .env
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`).

Set `VITE_API_BASE_URL` to the backend API root, including the version prefix. Default:
`http://localhost:8000/api/v1`.

Build for production:

```bash
npm run build
npm run preview
```

## API calls used

| UI action | Request |
|---|---|
| Company list | `GET /campaigns` |
| Company details and flows | `GET /campaigns/{campaign_id}` |
| Create company | `POST /campaigns` |
| Keitaro offer dropdown | `GET /offers` |
| Local offers counter | `GET /offers/local` |
| Fetch bindings from Keitaro | `POST /offers/sync/from-keitaro` |
| Sync bindings to Keitaro | `POST /offers/sync/to-keitaro` |

The UI normalizes common response variants (`items`, `data`, `flows` / `streams`, `offers` / `offer_bindings`). If your Pydantic response uses different property names, update the small mapping helpers in `src/api.js`.

## Backend contract gaps found in the supplied archive

The attached archive contains `campaigns.py`, `offers.py`, and `resources.py`, but it does **not** contain the schemas or service implementations. Also, the archive currently has no active endpoint for editing an offer binding on a specific flow.

The `PUT /streams/{stream_id}` handler shown in `campaigns.py` is commented out. Even if enabled as written, it proxies the update to Keitaro; it is not by itself proof that the local `FlowOffer` records are updated. The UI's flow editor currently calls:

`PUT /campaigns/streams/{stream_id}`

This path is the path implied by the commented router declaration (`router` prefix is `/campaigns`). Before using Add / Remove / Save in production, expose a backend endpoint that updates local flow-offer bindings in the database, then point `api.updateFlow()` in `src/api.js` to that endpoint. The two sync endpoints can then transfer the persisted local changes in either direction.

The `KTCampaignCreateRequest` schema was not included. The create form currently sends:

```json
{
  "name": "test_company_de",
  "geo": "DE",
  "offer_ids": [123, 456]
}
```

If the actual request schema uses different names or a nested flow payload, adjust the `payload` mapping in the `create` handler in `src/App.jsx`. This is intentionally isolated to one place.

## Notes

- Offer options are loaded from Keitaro (`GET /offers`).
- Flow offer edits are staged in the page until Save is clicked.
- Fetch and Sync call the supplied backend endpoints and refresh the current company after completion.
- The frontend does not contain credentials or a Keitaro token; those remain on the backend.
