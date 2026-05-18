import redis

from backend.core.config import settings


def is_queue_available() -> bool:
    client = redis.Redis.from_url(
        settings.celery_broker_url,
        socket_connect_timeout=2,
        socket_timeout=2,
    )

    try:
        return bool(client.ping())
    except redis.RedisError:
        return False
