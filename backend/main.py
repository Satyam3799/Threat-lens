from backend.database import Base, engine
from backend.models.user import User
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from backend.core.audit import configure_audit_logging
from backend.core.config import settings
from backend.core.queue_health import is_queue_available
from backend.core.rate_limit import limiter
from backend.models.scan import Scan
from backend.migrations import run_startup_migrations
from backend.routers.auth import router as auth_router
from backend.routers.intel import router as intel_router
from backend.routers.scan import router as scan_router


API_PREFIX = "/api"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown hooks."""
    configure_audit_logging()
    Base.metadata.create_all(bind=engine)
    run_startup_migrations()
    app.state.ready = True
    yield


app = FastAPI(
    title="Threat Lens API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/queue", tags=["health"])
async def queue_health() -> dict[str, str]:
    return {"status": "ok" if is_queue_available() else "unavailable"}


def register_routers(application: FastAPI) -> None:
    api_router = APIRouter(prefix=API_PREFIX)

    api_router.include_router(auth_router)
    api_router.include_router(scan_router)
    api_router.include_router(intel_router)
    application.include_router(api_router)


register_routers(app)
