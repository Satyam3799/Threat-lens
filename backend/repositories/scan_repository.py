from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from backend.models.scan import Scan


class ScanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_queued(self, target: str, user_id: int, scanner: str = "nmap") -> Scan:
        scan = Scan(target=target, user_id=user_id, status="queued", scanner=scanner)
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def mark_running(self, scan: Scan) -> Scan:
        scan.status = "running"
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def set_task_id(self, scan: Scan, celery_task_id: str) -> Scan:
        scan.celery_task_id = celery_task_id
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def mark_completed(
        self,
        scan: Scan,
        open_ports: list[dict],
        raw_result: dict,
        duration_ms: int,
    ) -> Scan:
        scan.status = "completed"
        scan.open_ports = open_ports
        scan.raw_result = raw_result
        scan.duration_ms = duration_ms
        scan.error_message = None
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def mark_failed(self, scan: Scan, error_message: str, duration_ms: int) -> Scan:
        scan.status = "failed"
        scan.error_message = error_message
        scan.duration_ms = duration_ms
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def set_open_ports_enriched(self, scan: Scan, data: dict[str, Any] | None) -> Scan:
        scan.open_ports_enriched = data
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def get_for_user(self, scan_id: int, user_id: int) -> Scan | None:
        statement = select(Scan).where(Scan.id == scan_id, Scan.user_id == user_id)
        return self.db.scalar(statement)

    def list_recent_for_user(self, user_id: int, limit: int = 25) -> list[Scan]:
        statement = (
            select(Scan)
            .where(Scan.user_id == user_id)
            .order_by(desc(Scan.created_at))
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def count_active_for_user(self, user_id: int) -> int:
        statement = select(func.count()).select_from(Scan).where(
            Scan.user_id == user_id,
            Scan.status.in_(["queued", "running"]),
        )
        return self.db.scalar(statement) or 0

    def count_active_global(self) -> int:
        statement = select(func.count()).select_from(Scan).where(
            Scan.status.in_(["queued", "running"]),
        )
        return self.db.scalar(statement) or 0
