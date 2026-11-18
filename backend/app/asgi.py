"""ASGI server entry point. Run with: uvicorn app.asgi:app"""

from app.main import get_app
from starlette.types import ASGIApp

app: ASGIApp = get_app()
