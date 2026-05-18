from datetime import datetime
import ipaddress
import re
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator


DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


class ScanCreate(BaseModel):
    target: str = Field(min_length=1, max_length=255)

    @field_validator("target")
    @classmethod
    def normalize_target(cls, value: str) -> str:
        target = value.strip()
        parsed = urlparse(target if "://" in target else f"//{target}")
        host = parsed.hostname or target
        host = host.strip().rstrip(".").lower()

        try:
            ipaddress.ip_address(host)
            return host
        except ValueError:
            pass

        if not DOMAIN_RE.fullmatch(host):
            raise ValueError("Target must be a valid IP address or domain.")

        return host


class PortService(BaseModel):
    model_config = ConfigDict(extra="ignore")

    port: int
    protocol: str
    state: str
    service: str | None = None
    product: str | None = None
    version: str | None = None
    extrainfo: str | None = None
    version_fingerprint: str | None = None


class ScanRead(BaseModel):
    id: int
    user_id: int
    target: str
    status: str
    scanner: str
    open_ports: list[PortService]
    error_message: str | None
    duration_ms: int | None
    created_at: datetime
    updated_at: datetime
    open_ports_enriched: dict[str, Any] | None = None


class ScanHistoryItem(BaseModel):
    id: int
    user_id: int
    target: str
    status: str
    scanner: str
    open_ports_count: int
    duration_ms: int | None
    created_at: datetime
