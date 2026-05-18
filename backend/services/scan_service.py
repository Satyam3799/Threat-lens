from time import perf_counter

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.integrations.scanners.nmap_scanner import (
    NmapScanner,
    ScannerExecutionError,
    ScannerUnavailableError,
)
from backend.core.audit import audit_event
from backend.core.config import settings
from backend.models.scan import Scan
from backend.repositories.scan_repository import ScanRepository
from backend.utils.targets import validate_scan_target_allowed

logger = logging.getLogger(__name__)


class ScanService:
    def __init__(
        self,
        db: Session,
        scanner: NmapScanner | None = None,
    ) -> None:
        self.repository = ScanRepository(db)
        self.scanner = scanner or NmapScanner()

    def queue_scan(self, target: str, user_id: int) -> Scan:
        validate_scan_target_allowed(target)
        user_active_scans = self.repository.count_active_for_user(user_id)
        if user_active_scans >= settings.max_user_active_scans:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="User active scan limit reached. Wait for a scan to finish before creating another.",
            )

        global_active_scans = self.repository.count_active_global()
        if global_active_scans >= settings.max_global_active_scans:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Global scan capacity reached. Try again later.",
            )

        scan = self.repository.create_queued(target=target, user_id=user_id, scanner=self.scanner.name)
        audit_event("scan.queued", user_id=user_id, scan_id=scan.id, target=target, status=scan.status)
        return scan

    def set_task_id(self, scan_id: int, user_id: int, celery_task_id: str) -> None:
        scan = self.repository.get_for_user(scan_id, user_id)
        if scan is None:
            return

        self.repository.set_task_id(scan, celery_task_id)

    def fail_scan(self, scan_id: int, user_id: int, error_message: str) -> None:
        scan = self.repository.get_for_user(scan_id, user_id)
        if scan is None or scan.status == "completed":
            return

        failed_scan = self.repository.mark_failed(scan, error_message, duration_ms=scan.duration_ms or 0)
        audit_event(
            "scan.failed",
            user_id=user_id,
            scan_id=failed_scan.id,
            target=failed_scan.target,
            status=failed_scan.status,
            error=error_message,
        )

    def execute_scan(self, scan_id: int, user_id: int) -> None:
        scan = self.repository.get_for_user(scan_id, user_id)
        if scan is None:
            return

        self.repository.mark_running(scan)
        audit_event("scan.running", user_id=user_id, scan_id=scan.id, target=scan.target, status=scan.status)
        started_at = perf_counter()

        try:
            result = self.scanner.scan(scan.target)
        except ScannerUnavailableError as exc:
            duration_ms = self._elapsed_ms(started_at)
            self.repository.mark_failed(scan, str(exc), duration_ms)
            audit_event(
                "scan.failed",
                user_id=user_id,
                scan_id=scan.id,
                target=scan.target,
                status="failed",
                error=str(exc),
                duration_ms=duration_ms,
            )
            return
        except ScannerExecutionError as exc:
            duration_ms = self._elapsed_ms(started_at)
            self.repository.mark_failed(scan, str(exc), duration_ms)
            audit_event(
                "scan.failed",
                user_id=user_id,
                scan_id=scan.id,
                target=scan.target,
                status="failed",
                error=str(exc),
                duration_ms=duration_ms,
            )
            return

        completed_scan = self.repository.mark_completed(
            scan=scan,
            open_ports=result.open_ports,
            raw_result=result.raw_result,
            duration_ms=self._elapsed_ms(started_at),
        )
        audit_event(
            "scan.completed",
            user_id=user_id,
            scan_id=completed_scan.id,
            target=completed_scan.target,
            status=completed_scan.status,
            open_ports_count=len(completed_scan.open_ports or []),
            duration_ms=completed_scan.duration_ms,
        )

        if settings.enable_intel_enrichment:
            try:
                from backend.intel.intel_service import enrich_scan

                enriched = enrich_scan(completed_scan)
                self.repository.set_open_ports_enriched(completed_scan, enriched)
            except Exception as exc:  # noqa: BLE001 — intel persistence must not fail scan completion
                logger.warning("Intel enrichment failed for scan %s: %s", completed_scan.id, exc)

    def get_scan(self, scan_id: int, user_id: int) -> Scan:
        scan = self.repository.get_for_user(scan_id, user_id)
        if scan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")

        return scan

    def list_history(self, user_id: int, limit: int = 25) -> list[Scan]:
        return self.repository.list_recent_for_user(user_id=user_id, limit=limit)

    @staticmethod
    def _elapsed_ms(started_at: float) -> int:
        return int((perf_counter() - started_at) * 1000)
