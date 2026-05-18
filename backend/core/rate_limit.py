from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.core.config import settings
from backend.utils.security import try_decode_jwt_subject_for_rate_limit


def rate_limit_by_user_or_ip(request: Request) -> str:
    subject = try_decode_jwt_subject_for_rate_limit(request.headers.get("Authorization"))
    if subject:
        return f"jwt_sub:{subject}"
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.default_rate_limit],
)
