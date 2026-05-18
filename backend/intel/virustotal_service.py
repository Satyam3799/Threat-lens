from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from backend.core.config import settings

logger = logging.getLogger(__name__)

VT_BASE = "https://www.virustotal.com/api/v3"


def _last_analysis_stats(payload: dict[str, Any]) -> dict[str, int] | None:
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    attrs = data.get("attributes")
    if not isinstance(attrs, dict):
        return None
    stats = attrs.get("last_analysis_stats")
    if not isinstance(stats, dict):
        return None
    return stats


def get_ip_report(ip: str) -> dict[str, Any] | None:
    """VirusTotal IP report; returns normalized scores or None on failure."""
    if not settings.vt_api_key or not settings.vt_api_key.strip():
        return None

    encoded = urllib.parse.quote(ip.strip(), safe="")
    url = f"{VT_BASE}/ip_addresses/{encoded}"

    headers = {"x-apikey": settings.vt_api_key.strip(), "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=settings.intel_http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("VirusTotal IP lookup failed: %s", exc)
        return None

    if not isinstance(payload, dict):
        return None

    stats = _last_analysis_stats(payload)
    if stats is None:
        return None

    def _int(key: str) -> int:
        val = stats.get(key)
        return int(val) if isinstance(val, int) else 0

    return {
        "malicious_score": _int("malicious"),
        "suspicious_score": _int("suspicious"),
        "harmless_score": _int("harmless"),
    }


def get_domain_report(domain: str) -> dict[str, Any] | None:
    """VirusTotal domain report; returns normalized scores or None on failure."""
    if not settings.vt_api_key or not settings.vt_api_key.strip():
        return None

    encoded = urllib.parse.quote(domain.strip().lower(), safe="")
    url = f"{VT_BASE}/domains/{encoded}"

    headers = {"x-apikey": settings.vt_api_key.strip(), "Accept": "application/json"}
    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=settings.intel_http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("VirusTotal domain lookup failed: %s", exc)
        return None

    if not isinstance(payload, dict):
        return None

    stats = _last_analysis_stats(payload)
    if stats is None:
        return None

    def _int(key: str) -> int:
        val = stats.get(key)
        return int(val) if isinstance(val, int) else 0

    return {
        "malicious_score": _int("malicious"),
        "suspicious_score": _int("suspicious"),
        "harmless_score": _int("harmless"),
    }
