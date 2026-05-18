from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.core.audit import audit_event, get_client_ip
from backend.core.config import settings
from backend.core.rate_limit import limiter
from backend.database import get_db
from backend.schemas.auth import Token, UserCreate, UserLogin, UserRead
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.auth_register_rate_limit)
def register(
    request: Request,
    user_create: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    try:
        user = auth_service.register_user(user_create)
    except HTTPException as exc:
        audit_event(
            "auth.register.failed",
            email=user_create.email,
            client_ip=get_client_ip(request),
            status_code=exc.status_code,
        )
        raise

    audit_event("auth.register.succeeded", user_id=user.id, email=user.email, client_ip=get_client_ip(request))
    return user


@router.post("/login", response_model=Token)
@limiter.limit(settings.auth_login_rate_limit)
def login(
    request: Request,
    credentials: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> Token:
    try:
        token = auth_service.login(credentials)
    except HTTPException as exc:
        audit_event(
            "auth.login.failed",
            email=credentials.email,
            client_ip=get_client_ip(request),
            status_code=exc.status_code,
        )
        raise

    audit_event("auth.login.succeeded", email=credentials.email, client_ip=get_client_ip(request))
    return token
