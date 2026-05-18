from __future__ import annotations

from typing import Any


def get_nessus_recommendation(service: str, version: str | None = None) -> dict[str, Any]:
    """Stub Nessus integration — enterprise scanning guidance only."""
    return {
        "manual_scan_required": True,
        "reason": "Enterprise scanner required for deep vuln analysis",
        "service": service,
        "version": version,
    }
