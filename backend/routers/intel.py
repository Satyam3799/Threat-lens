from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request

from backend.core.config import settings
from backend.core.rate_limit import limiter, rate_limit_by_user_or_ip
from backend.intel.cve_service import search_cves_by_keyword
from backend.intel.shodan_service import get_host_intel
from backend.intel.virustotal_service import get_ip_report
from backend.models.user import User
from backend.utils.security import get_current_user
from backend.utils.validators import sanitize_intel_keyword, validate_ip

router = APIRouter(prefix="/intel", tags=["intel"])


@router.get("/cve")
@limiter.limit(settings.intel_endpoint_rate_limit, key_func=rate_limit_by_user_or_ip)
def intel_cve_lookup(
    request: Request,
    keyword: Annotated[str, Query(min_length=1, max_length=200)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[dict[str, Any]]:
    _ = (request, current_user)
    safe = sanitize_intel_keyword(keyword)
    return search_cves_by_keyword(safe)


@router.get("/shodan")
@limiter.limit(settings.intel_endpoint_rate_limit, key_func=rate_limit_by_user_or_ip)
def intel_shodan_lookup(
    request: Request,
    ip: Annotated[str, Query(min_length=3, max_length=45)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any] | None:
    _ = (request, current_user)
    normalized = validate_ip(ip, allow_private=False)
    return get_host_intel(normalized)


@router.get("/virustotal/ip")
@limiter.limit(settings.intel_endpoint_rate_limit, key_func=rate_limit_by_user_or_ip)
def intel_virustotal_ip(
    request: Request,
    ip: Annotated[str, Query(min_length=3, max_length=45)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any] | None:
    _ = (request, current_user)
    normalized = validate_ip(ip, allow_private=False)
    return get_ip_report(normalized)
