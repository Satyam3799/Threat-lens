from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from fastapi import HTTPException, status

from backend.schemas.scan import DOMAIN_RE


def _is_public_ip(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def validate_ip(value: str, *, allow_private: bool = True) -> str:
    """Return normalized IP string or raise HTTPException."""
    raw = value.strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="IP address is required.")
    try:
        addr = ipaddress.ip_address(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid IP address.",
        ) from exc

    if not allow_private and not _is_public_ip(addr):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Private, loopback, or reserved IP addresses are not allowed for this operation.",
        )

    return str(addr)


def validate_domain(value: str, *, max_length: int = 253) -> str:
    """Return normalized hostname or raise HTTPException."""
    raw = value.strip().lower().rstrip(".")
    if not raw or len(raw) > max_length:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid domain.")
    try:
        ipaddress.ip_address(raw)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expected a domain name, not an IP address.",
        )
    except ValueError:
        pass

    if not DOMAIN_RE.fullmatch(raw):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid domain name.")

    return raw


def validate_url(value: str, *, max_length: int = 2048) -> str:
    """Return a sanitized http(s) URL string or raise HTTPException."""
    raw = value.strip()
    if not raw or len(raw) > max_length:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL.")

    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must use http or https scheme.",
        )

    if not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL is missing a host.")

    host = parsed.hostname
    if not host:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL is missing a host.")

    if host in {"localhost"} or host.endswith(".local"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Local URLs are not allowed.")

    try:
        addr = ipaddress.ip_address(host)
        if not _is_public_ip(addr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Private or reserved IP URLs are not allowed.",
            )
    except ValueError:
        validate_domain(host)

    return raw


def sanitize_intel_keyword(value: str, *, max_length: int = 200) -> str:
    """Restrict free-text intel keywords to safe characters."""
    raw = value.strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keyword is required.")
    if len(raw) > max_length:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keyword is too long.")

    if not re.match(r"^[\w\s\.\-\+/:@]+$", raw, re.UNICODE):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keyword contains invalid characters.")

    return raw


def parse_ip_or_none(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def is_public_ip_string(value: str) -> bool:
    addr = parse_ip_or_none(value)
    return bool(addr and _is_public_ip(addr))


def normalize_public_ip(value: str) -> str | None:
    """Return normalized public IP string, or None if invalid / non-public."""
    addr = parse_ip_or_none(value)
    if addr is None or not _is_public_ip(addr):
        return None
    return str(addr)
