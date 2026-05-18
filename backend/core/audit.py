from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from typing import Any

from fastapi import Request


AUDIT_LOGGER_NAME = "threat_lens.audit"


class JsonAuditFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
            "logger": record.name,
        }

        context = getattr(record, "context", None)
        if isinstance(context, dict):
            payload.update(context)

        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_audit_logging() -> None:
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonAuditFormatter())
    logger.addHandler(handler)


def get_client_ip(request: Request | None) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()

    return request.client.host if request.client else None


def audit_event(event: str, **context: Any) -> None:
    logging.getLogger(AUDIT_LOGGER_NAME).info(
        event,
        extra={"event": event, "context": context},
    )
