from celery import Celery

from backend.core.config import settings


celery_app = Celery(
    "threat_lens",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.worker.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_always_eager=settings.celery_task_always_eager,
    task_time_limit=settings.scan_timeout_seconds + 30,
    task_soft_time_limit=settings.scan_timeout_seconds + 15,
    broker_connection_timeout=10,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "socket_connect_timeout": 10,
        "socket_timeout": 10,
        "retry_on_timeout": True,
    },
    task_publish_retry=True,
)
