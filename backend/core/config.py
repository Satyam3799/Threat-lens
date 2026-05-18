from dataclasses import dataclass
import os


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


def _get_cors_origins() -> tuple[str, ...]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))
    celery_task_always_eager: bool = _get_bool_env("CELERY_TASK_ALWAYS_EAGER", default=False)
    scan_timeout_seconds: int = _get_int_env("SCAN_TIMEOUT_SECONDS", 120)
    max_global_active_scans: int = _get_int_env("MAX_GLOBAL_ACTIVE_SCANS", 4)
    max_user_active_scans: int = _get_int_env("MAX_USER_ACTIVE_SCANS", 1)
    scan_create_rate_limit: str = os.getenv("SCAN_CREATE_RATE_LIMIT", "5/minute")
    auth_login_rate_limit: str = os.getenv("AUTH_LOGIN_RATE_LIMIT", "10/minute")
    auth_register_rate_limit: str = os.getenv("AUTH_REGISTER_RATE_LIMIT", "3/minute")
    default_rate_limit: str = os.getenv("DEFAULT_RATE_LIMIT", "120/minute")
    intel_endpoint_rate_limit: str = os.getenv("INTEL_ENDPOINT_RATE_LIMIT", "20/minute")
    cors_origins: tuple[str, ...] = _get_cors_origins()
    allow_private_scan_targets: bool = _get_bool_env("ALLOW_PRIVATE_SCAN_TARGETS", default=True)
    full_port_scan_enabled: bool = _get_bool_env("FULL_PORT_SCAN_ENABLED", default=False)
    enable_intel_enrichment: bool = _get_bool_env("ENABLE_INTEL_ENRICHMENT", default=False)
    shodan_api_key: str = os.getenv("SHODAN_API_KEY", "")
    vt_api_key: str = os.getenv("VT_API_KEY", "")
    nvd_api_key: str = os.getenv("NVD_API_KEY", "")
    intel_http_timeout_seconds: int = _get_int_env("INTEL_HTTP_TIMEOUT_SECONDS", 12)

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"


settings = Settings()
