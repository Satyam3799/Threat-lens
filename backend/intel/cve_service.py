from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from backend.core.config import settings

logger = logging.getLogger(__name__)

NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _severity_from_score(score: float | None) -> str:
    if score is None:
        return "LOW"
    if score >= 9.0:
        return "CRITICAL"
    if score >= 7.0:
        return "HIGH"
    if score >= 4.0:
        return "MEDIUM"
    return "LOW"


def _extract_cvss_score_and_severity(cve_item: dict[str, Any]) -> tuple[float | None, str]:
    """Extract primary CVSS base score and severity from a NVD CVE JSON object."""
    metrics = cve_item.get("metrics") or {}
    for version_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        arr = metrics.get(version_key)
        if not isinstance(arr, list) or not arr:
            continue
        first = arr[0]
        data = first.get("cvssData") if isinstance(first, dict) else None
        if not isinstance(data, dict):
            continue
        base = data.get("baseScore")
        if isinstance(base, (int, float)):
            score = float(base)
            return score, _severity_from_score(score)

    return None, "LOW"


def parse_cvss_score(cve_response: dict[str, Any]) -> dict[str, Any]:
    """Public helper: map raw NVD `cve` object to score + severity."""
    score, severity = _extract_cvss_score_and_severity(cve_response)
    return {"cvss_score": score, "severity": severity}


def _english_description(cve_item: dict[str, Any]) -> str:
    descriptions = cve_item.get("descriptions") or []
    for desc in descriptions:
        if isinstance(desc, dict) and desc.get("lang") == "en":
            return str(desc.get("value") or "").strip()
    if descriptions and isinstance(descriptions[0], dict):
        return str(descriptions[0].get("value") or "").strip()
    return ""


def get_cves_by_keyword(service: str, version: str | None = None) -> list[dict[str, Any]]:
    """
    Query NVD CVE 2.0 API by keyword (service + optional version).
    Returns normalized CVE dicts; empty list on any failure.
    """
    parts = [service.strip()]
    if version:
        parts.append(str(version).strip())
    keyword = " ".join(p for p in parts if p).strip()
    return search_cves_by_keyword(keyword)


def search_cves_by_keyword(keyword: str) -> list[dict[str, Any]]:
    """Single-keyword NVD search (used by HTTP intel routes)."""
    keyword = keyword.strip()
    if not keyword:
        return []

    params = urllib.parse.urlencode({"keywordSearch": keyword, "resultsPerPage": 15})
    url = f"{NVD_CVE_URL}?{params}"

    headers = {"Accept": "application/json"}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key

    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=settings.intel_http_timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("NVD CVE lookup failed: %s", exc)
        return []

    vulnerabilities = payload.get("vulnerabilities")
    if not isinstance(vulnerabilities, list):
        return []

    normalized: list[dict[str, Any]] = []
    for entry in vulnerabilities:
        if not isinstance(entry, dict):
            continue
        cve_wrap = entry.get("cve")
        if not isinstance(cve_wrap, dict):
            continue
        cve_id = cve_wrap.get("id")
        if not isinstance(cve_id, str):
            continue

        score, severity = _extract_cvss_score_and_severity(cve_wrap)
        normalized.append(
            {
                "cve_id": cve_id,
                "description": _english_description(cve_wrap),
                "cvss_score": score,
                "severity": severity,
            }
        )

    return normalized
