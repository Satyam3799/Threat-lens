from __future__ import annotations

import logging
import socket
from typing import Any

from backend.core.config import settings
from backend.intel.cve_service import get_cves_by_keyword
from backend.intel.nessus_stub import get_nessus_recommendation
from backend.intel.shodan_service import get_host_intel
from backend.intel.virustotal_service import get_domain_report, get_ip_report
from backend.models.scan import Scan
from backend.utils.validators import normalize_public_ip, parse_ip_or_none

logger = logging.getLogger(__name__)


def _service_version_string(port: dict[str, Any]) -> str | None:
    fp = port.get("version_fingerprint")
    if isinstance(fp, str) and fp.strip():
        return fp.strip()
    parts = [port.get("product"), port.get("version"), port.get("extrainfo")]
    joined = " ".join(str(p).strip() for p in parts if p)
    return joined or None


def _resolve_public_ip_for_target(target: str) -> str | None:
    direct = normalize_public_ip(target)
    if direct:
        return direct

    try:
        infos = socket.getaddrinfo(target, None)
    except OSError:
        return None

    for item in infos:
        addr = item[4][0]
        normalized = normalize_public_ip(addr)
        if normalized:
            return normalized
    return None


def enrich_scan(scan: Scan) -> dict[str, Any]:
    """
    Build intel enrichment from a completed scan record.
    Never raises — external failures degrade to empty / null fields.
    """
    if not settings.enable_intel_enrichment:
        return {"enabled": False, "ports": [], "shodan": None, "virustotal": None}

    open_ports = scan.open_ports or []
    ports_out: list[dict[str, Any]] = []

    for port in open_ports:
        if not isinstance(port, dict):
            continue

        service_name = str(port.get("service") or port.get("name") or "unknown")
        version = _service_version_string(port)

        try:
            cves = get_cves_by_keyword(service_name, version)
        except Exception as exc:  # noqa: BLE001 — intel must never break scan
            logger.warning("CVE enrichment failed for port: %s", exc)
            cves = []

        try:
            nessus = get_nessus_recommendation(service_name, version)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Nessus stub failed: %s", exc)
            nessus = {
                "manual_scan_required": True,
                "reason": "Enterprise scanner required for deep vuln analysis",
            }

        row = {**port, "cves": cves, "nessus": nessus}
        ports_out.append(row)

    shodan_data = None
    vt_data = None

    try:
        if parse_ip_or_none(scan.target):
            pub = normalize_public_ip(scan.target)
            if pub:
                shodan_data = get_host_intel(pub)
                vt_data = get_ip_report(pub)
        else:
            vt_data = get_domain_report(scan.target)
            pub = _resolve_public_ip_for_target(scan.target)
            if pub:
                shodan_data = get_host_intel(pub)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Host intel enrichment failed: %s", exc)

    return {
        "enabled": True,
        "ports": ports_out,
        "shodan": shodan_data,
        "virustotal": vt_data,
    }
