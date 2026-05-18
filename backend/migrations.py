from sqlalchemy import text

from backend.database import engine


def run_startup_migrations() -> None:
    """Small compatibility migrations until Alembic is added."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE IF EXISTS scans
                ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_scans_user_id
                ON scans (user_id)
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE IF EXISTS scans
                ADD COLUMN IF NOT EXISTS celery_task_id VARCHAR(255)
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_scans_celery_task_id
                ON scans (celery_task_id)
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE IF EXISTS scans
                ADD COLUMN IF NOT EXISTS open_ports_enriched JSON
                """
            )
        )
