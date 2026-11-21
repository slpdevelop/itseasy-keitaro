# Keitaro Campaign Manager - Backend

FastAPI backend for managing Keitaro campaigns.

## Requirements

- Python 3.13+
- pip (package manager)

## Installation

```bash
cd backend
python -m venv .venv
.\venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Unix

pip install -e ".[dev,test]"
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

- `APP_NAME` — application name
- `KEITARO_BASE_URL` — Keitaro API URL

For development, Keitaro API token is not required. For production, configure `KEITARO_API_TOKEN`.

## Running with Docker (recommended)

The entire stack (PostgreSQL + FastAPI backend + React frontend) starts with one command:

```bash
cd backend
docker compose up -d --build   # build images and start DB + backend + frontend
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
docker compose up -d           # only PostgreSQL

# In activated venv
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

Settings are read from `backend/.env`: `USE_POSTGRESQL=True` and `POSTGRES_*`
(`POSTGRES_PASSWORD` is required and must match the container password).

On application startup in `lifespan`:

- database is created (if it does not exist yet);
- connection is established and verified (`SELECT 1`);
- if the database is unavailable, startup fails (retries until the container starts);
- on application shutdown, the connection is closed properly.

If `USE_POSTGRESQL=False`, no database connection is established.

## Testing

```bash
# In activated venv
pytest app/tests/ -v --cov=app --cov-report=html
```

Test coverage: **86% and above**.

## Project structure

```
backend/
├── app/                     # FastAPI application
│   ├── main.py              # FastAPI entry point
│   ├── api/                 # Routes
│   ├── core/                # Configuration, database, exceptions
│   ├── integrations/        # Keitaro adapters
│   ├── interfaces/          # Protocol contracts for gateways
│   ├── repositories/        # SQLAlchemy repositories
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business services
│   └── tests/               # Tests
├── alembic/                 # Database migrations
├── .env.example             # Configuration example (copy to .env)
├── .env                     # Your secrets (do not commit!)
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
├── .env                     # VITE_API_BASE_URL
├── .dockerignore
├── Dockerfile               # Vite build + served via nginx
├── nginx.conf               # Proxies /api to backend, SPA fallback
├── package.json
└── README.md
```

## Development plan

See [`PLAN.md`](../PLAN.md) for implementation details:

- **Stage 0:** Repository analysis ✅
- **Stage 1:** Python environment ✅
- **Stage 2:** FastAPI scaffold ✅
- **Stage 3:** Configuration and security ✅
- **Stage 4+:** In development

## License

[ICVR license](../ICVR_LICENSE)
