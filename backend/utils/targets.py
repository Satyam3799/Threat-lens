import ipaddress
import socket

from fastapi import HTTPException, status

from backend.core.config import settings


def validate_scan_target_allowed(target: str) -> None:
    addresses = _resolve_target_addresses(target)
    blocked_addresses = [
        address
        for address in addresses
        if _is_blocked_address(address)
    ]

    if blocked_addresses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Target resolves to a private, loopback, link-local, multicast, "
                "or reserved address. Set ALLOW_PRIVATE_SCAN_TARGETS=true only "
                "for trusted local environments."
            ),
        )


def _resolve_target_addresses(target: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return [ipaddress.ip_address(target)]
    except ValueError:
        pass

    try:
        resolved = socket.getaddrinfo(target, None)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target domain could not be resolved.",
        ) from exc

    addresses = sorted({item[4][0] for item in resolved})
    return [ipaddress.ip_address(address) for address in addresses]


def _is_blocked_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if settings.allow_private_scan_targets:
        return False

    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )
