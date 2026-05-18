from collections.abc import Generator
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
DATABASE_URL_ENV = "DATABASE_URL"
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30

if ROOT_ENV_PATH.is_file():
    load_dotenv(ROOT_ENV_PATH)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc


def _database_url_from_parts() -> URL | None:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    database = os.getenv("POSTGRES_DB")

    if not all((user, password, host, database)):
        return None

    return URL.create(
        drivername=os.getenv("POSTGRES_DRIVER", "postgresql+psycopg2"),
        username=user,
        password=password,
        host=host,
        port=_get_int_env("POSTGRES_PORT", 5432),
        database=database,
    )


def _default_sslmode(database_url: URL) -> str:
    if database_url.host in {"localhost", "127.0.0.1", "::1", "postgres"}:
        return "disable"

    return "require"


def get_database_url() -> URL:
    raw_url = os.getenv(DATABASE_URL_ENV)
    database_url = make_url(raw_url) if raw_url else _database_url_from_parts()

    if database_url is None:
        raise RuntimeError(
            "Set DATABASE_URL or POSTGRES_USER, POSTGRES_PASSWORD, "
            "POSTGRES_HOST, and POSTGRES_DB before starting the backend."
        )

    if not database_url.drivername.startswith("postgresql"):
        raise RuntimeError("Database URL must use a PostgreSQL SQLAlchemy driver.")

    if "sslmode" not in database_url.query:
        sslmode = os.getenv("POSTGRES_SSLMODE", _default_sslmode(database_url))
        database_url = database_url.update_query_dict({"sslmode": sslmode})

    return database_url


SQLALCHEMY_DATABASE_URL = get_database_url()

engine: Engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=_get_bool_env("SQLALCHEMY_ECHO", default=False),
    future=True,
    pool_pre_ping=True,
    pool_size=_get_int_env("SQLALCHEMY_POOL_SIZE", DEFAULT_POOL_SIZE),
    max_overflow=_get_int_env("SQLALCHEMY_MAX_OVERFLOW", DEFAULT_MAX_OVERFLOW),
    pool_timeout=_get_int_env("SQLALCHEMY_POOL_TIMEOUT", DEFAULT_POOL_TIMEOUT),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
