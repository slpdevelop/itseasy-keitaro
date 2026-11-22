# Keitaro Campaign Manager - Backend

FastAPI backend for managing Keitaro campaigns.

## Requirements

- Python 3.11+
- pip (package manager)

## Installation

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Unix

pip install -e ".[dev]"
```

## Configuration

Create `backend/.env` based on `.env.example`:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your values
```

**Important:** Never commit real secrets to Git!  
Files `.env`, `.env.*` and `backend/.env*` are excluded from Git via `.gitignore`.

### Required environment variables:

- `KEITARO_BASE_URL` — Keitaro Admin API URL
- `KEITARO_API_TOKEN` — Keitaro API token (required in every environment)
- `POSTGRES_DB_URL` — async PostgreSQL DSN
- `POSTGRES_PASSWORD` — PostgreSQL container password when using Compose

## Running with Docker (recommended)

The entire stack (PostgreSQL + FastAPI backend + React frontend) starts with one command:

```bash
cd backend
docker compose up -d --build   # build images and start DB + backend + frontend
# ENV=production in backend/.env disables reload and builds the static frontend
docker compose ps              # all three services should be healthy
docker compose logs -f app     # backend logs
docker compose logs -f frontend
docker compose down            # stop (database data persists in volume)
```

- Backend (FastAPI): `http://localhost:8000` (health: `/health`, docs: `/docs`)
- Frontend (React + Vite, nginx): `http://localhost:5173` — proxies `/api` to backend
- PostgreSQL: `localhost:5432`, database created automatically on startup
- Settings are read from `backend/.env` (via `env_file`); secrets do not end up
  in the image (excluded via `.dockerignore`)
- Startup order: PostgreSQL → healthcheck → backend (Alembic migrations applied,
  then uvicorn starts) → frontend; frontend waits until backend becomes healthy

## Running locally (without Docker for the application)

```bash
cd backend
docker compose up -d postgres  # only PostgreSQL

# In activated venv
alembic upgrade head
uvicorn app.asgi:app --reload --port 8000
```

API is available at `http://localhost:8000/api/v1`  
OpenAPI documentation (dev only): `http://localhost:8000/docs`

## PostgreSQL (Docker)

The database is started via Docker Compose (file `docker-compose.yml`):

```bash
cd backend
docker compose up -d     # start PostgreSQL
docker compose ps        # status (healthy)
docker compose down      # stop (data persists in volume)
```

Settings are read from `backend/.env`. `POSTGRES_DB_URL` must point to the
PostgreSQL service; `POSTGRES_PASSWORD` must match the container password.

On application startup in `lifespan`:

- the SQLAlchemy engine and session factory are initialized;
- Compose applies Alembic migrations before starting Uvicorn;
- `/health` executes `SELECT 1` and returns 503 when PostgreSQL is unavailable;
- on application shutdown, the connection is closed properly.

The backend requires PostgreSQL.

## Tests

Automated tests are not included in this delivery archive.

## Project structure

```
backend/
├── app/                     # FastAPI application
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # Routes
│   ├── core/                # Configuration, database, exceptions
│   ├── integrations/        # Keitaro adapters
│   ├── repositories/        # SQLAlchemy repositories
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business services
├── alembic/                 # Database migrations
├── .env.example             # Configuration example (copy to .env)
├── .dockerignore
├── Dockerfile               # Backend image
├── alembic.ini
├── docker-compose.yml       # Stack: PostgreSQL + backend + frontend
├── pyproject.toml
└── README.md
```

frontend/
├── src/                     # React + Vite sources
├── index.html
├── .dockerignore
├── Dockerfile               # Vite build + served via nginx
├── nginx.conf               # Proxies /api to backend, SPA fallback
├── package.json
└── README.md
```

## Synchronization and consistency

- Campaign creation validates the requested offer IDs before creating upstream resources.
- Creation checkpoints and idempotency state are stored in PostgreSQL for 24-hour replay protection.
- `sync` checks the remote flow state before pushing and reports conflicts as HTTP 207 with per-flow details.
- Local edits are staged in PostgreSQL; `POST /campaigns/{id}/sync` pushes them to Keitaro.
- Only non-deleted ACTIVE offers participate in the 100% allocation; DISABLED offers are retained with zero share.
- A sync preflight compares the current remote stream with the local snapshot. If they differ, the flow is not overwritten and the client must fetch/reconcile first.
