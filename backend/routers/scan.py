from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from kombu.exceptions import KombuError
from sqlalchemy.orm import Session

from backend.core.audit import audit_event, get_client_ip
from backend.core.config import settings
from backend.core.queue_health import is_queue_available
from backend.core.rate_limit import limiter, rate_limit_by_user_or_ip
from backend.database import get_db
from backend.models.scan import Scan
from backend.models.user import User
from backend.schemas.scan import ScanCreate, ScanHistoryItem, ScanRead
from backend.services.scan_service import ScanService
from backend.utils.security import get_current_user
from backend.worker.tasks import execute_scan_task


router = APIRouter(prefix="/scan", tags=["scan"])


def get_scan_service(db: Annotated[Session, Depends(get_db)]) -> ScanService:
    return ScanService(db)


def to_scan_read(scan: Scan) -> ScanRead:
    return ScanRead(
        id=scan.id,
        user_id=scan.user_id or 0,
        target=scan.target,
        status=scan.status,
        scanner=scan.scanner,
        open_ports=scan.open_ports,
        error_message=scan.error_message,
        duration_ms=scan.duration_ms,
        created_at=scan.created_at,
        updated_at=scan.updated_at,
        open_ports_enriched=scan.open_ports_enriched,
    )


def to_history_item(scan: Scan) -> ScanHistoryItem:
    return ScanHistoryItem(
        id=scan.id,
        user_id=scan.user_id or 0,
        target=scan.target,
        status=scan.status,
        scanner=scan.scanner,
        open_ports_count=len(scan.open_ports or []),
        duration_ms=scan.duration_ms,
        created_at=scan.created_at,
    )


@router.post("", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.scan_create_rate_limit)
def create_scan(
    payload: ScanCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
) -> ScanRead:
    if not is_queue_available():
        audit_event(
            "scan.queue_unavailable",
            user_id=current_user.id,
            target=payload.target,
            client_ip=get_client_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scan queue is unavailable. Ensure Redis and the Celery worker are running.",
        )

    scan = scan_service.queue_scan(payload.target, user_id=current_user.id)
    try:
        task = execute_scan_task.apply_async(args=[scan.id, current_user.id])
    except KombuError as exc:
        scan_service.fail_scan(scan.id, current_user.id, "Scan queue is unavailable.")
        audit_event(
            "scan.queue_unavailable",
            user_id=current_user.id,
            scan_id=scan.id,
            target=scan.target,
            client_ip=get_client_ip(request),
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scan queue is unavailable. Ensure Redis and the Celery worker are running.",
        ) from exc
    except Exception as exc:
        scan_service.fail_scan(scan.id, current_user.id, "Scan queue is unavailable.")
        audit_event(
            "scan.queue_unavailable",
            user_id=current_user.id,
            scan_id=scan.id,
            target=scan.target,
            client_ip=get_client_ip(request),
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scan queue is unavailable. Ensure Redis and the Celery worker are running.",
        ) from exc

    scan_service.set_task_id(scan.id, current_user.id, task.id)
    audit_event(
        "scan.enqueued",
        user_id=current_user.id,
        scan_id=scan.id,
        target=scan.target,
        client_ip=get_client_ip(request),
        celery_task_id=task.id,
    )
    return to_scan_read(scan)


@router.get("/history", response_model=list[ScanHistoryItem])
def scan_history(
    current_user: Annotated[User, Depends(get_current_user)],
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
) -> list[ScanHistoryItem]:
    return [to_history_item(scan) for scan in scan_service.list_history(user_id=current_user.id, limit=limit)]


@router.get("/{scan_id}/enriched", response_model=ScanRead)
@limiter.limit(settings.intel_endpoint_rate_limit, key_func=rate_limit_by_user_or_ip)
def get_scan_enriched(
    request: Request,
    scan_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
) -> ScanRead:
    _ = request
    return to_scan_read(scan_service.get_scan(scan_id, user_id=current_user.id))


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(
    scan_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    scan_service: Annotated[ScanService, Depends(get_scan_service)],
) -> ScanRead:
    return to_scan_read(scan_service.get_scan(scan_id, user_id=current_user.id))
