from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas.auth import Token, UserCreate, UserLogin
from backend.utils.security import create_access_token, hash_password, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_user(self, user_create: UserCreate) -> User:
        email = user_create.email.strip().lower()
        existing_user = self._get_user_by_email(email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )

        user = User(
            email=email,
            full_name=user_create.full_name,
            hashed_password=hash_password(user_create.password),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            ) from exc

        self.db.refresh(user)
        return user

    def login(self, credentials: UserLogin) -> Token:
        email = credentials.email.strip().lower()
        user = self._get_user_by_email(email)
        if user is None or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        access_token, expires_in = create_access_token(subject=str(user.id))
        return Token(access_token=access_token, expires_in=expires_in)

    def _get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.scalar(statement)
