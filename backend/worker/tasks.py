from celery.exceptions import SoftTimeLimitExceeded

from backend.core.audit import audit_event, configure_audit_logging
from backend.database import SessionLocal
from backend.services.scan_service import ScanService
from backend.worker.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2, default_retry_delay=20, name="scan.execute")
def execute_scan_task(self, scan_id: int, user_id: int) -> None:
    configure_audit_logging()
    audit_event("scan.worker.started", scan_id=scan_id, user_id=user_id, celery_task_id=self.request.id)

    try:
        with SessionLocal() as db:
            ScanService(db).execute_scan(scan_id=scan_id, user_id=user_id)
    except SoftTimeLimitExceeded:
        with SessionLocal() as db:
            ScanService(db).fail_scan(scan_id=scan_id, user_id=user_id, error_message="Scan worker timed out.")
        raise
    except Exception as exc:
        audit_event(
            "scan.worker.error",
            scan_id=scan_id,
            user_id=user_id,
            celery_task_id=self.request.id,
            error=str(exc),
            retry_count=self.request.retries,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        with SessionLocal() as db:
            ScanService(db).fail_scan(scan_id=scan_id, user_id=user_id, error_message=str(exc))
        raise
