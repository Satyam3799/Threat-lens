from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from backend.core.config import settings
from backend.utils.validators import normalize_public_ip

logger = logging.getLogger(__name__)

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, dict[str, Any] | None]] = {}
_CACHE_TTL_SECONDS = 600


def _cache_get(ip: str) -> dict[str, Any] | None | str:
    """Return cached dict, None sentinel for cached miss, or _MISS if absent."""
    now = time.monotonic()
    with _CACHE_LOCK:
        entry = _CACHE.get(ip)
        if not entry:
            return "_MISS"
        expires_at, data = entry
        if expires_at < now:
            del _CACHE[ip]
            return "_MISS"
        return data


def _cache_set(ip: str, data: dict[str, Any] | None) -> None:
    expires = time.monotonic() + _CACHE_TTL_SECONDS
    with _CACHE_LOCK:
        _CACHE[ip] = (expires, data)


def get_host_intel(ip: str) -> dict[str, Any] | None:
    """
    Fetch Shodan host metadata for a public IP.
    Returns normalized dict or None on failure / missing key / private IP.
    """
    if not settings.shodan_api_key:
        return None

    normalized_ip = normalize_public_ip(ip)
    if not normalized_ip:
        return None

    cached = _cache_get(normalized_ip)
    if cached != "_MISS":
        return cached

    if not settings.shodan_api_key.strip():
        return None

    qs = urllib.parse.urlencode({"key": settings.shodan_api_key.strip()})
    url = f"https://api.shodan.io/shodan/host/{urllib.parse.quote(normalized_ip)}?{qs}"

    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(request, timeout=settings.intel_http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Shodan host lookup failed: %s", exc)
        _cache_set(normalized_ip, None)
        return None

    if not isinstance(payload, dict):
        _cache_set(normalized_ip, None)
        return None

    ports: list[int] = []
    for item in payload.get("data") or []:
        if isinstance(item, dict) and "port" in item:
            try:
                ports.append(int(item["port"]))
            except (TypeError, ValueError):
                continue

    result = {
        "org": payload.get("org"),
        "isp": payload.get("isp"),
        "open_ports": sorted(set(ports)),
        "hostnames": payload.get("hostnames") or [],
        "tags": payload.get("tags") or [],
    }
    _cache_set(normalized_ip, result)
    return result
