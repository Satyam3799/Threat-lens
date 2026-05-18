from __future__ import annotations

import os

from backend.core.config import settings


def validate_settings_for_startup() -> None:
    """Fail fast when production is misconfigured."""
    if not settings.is_production:
        return

    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be at least 32 characters when APP_ENV=production."
        )

    if not settings.cors_origins:
        raise RuntimeError("CORS_ORIGINS must be set when APP_ENV=production.")

    if any(origin.startswith("http://") for origin in settings.cors_origins):
        raise RuntimeError(
            "Use HTTPS origins in CORS_ORIGINS for production (e.g. https://your.domain)."
        )
