from datetime import datetime, timezone

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.connection import settings
from models.revoked_token import RevokedToken
from models.user import User
from utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


def is_token_revoked(jti: str, db: Session) -> bool:
    return db.scalar(
        select(RevokedToken.id).where(RevokedToken.jti == jti)
    ) is not None


def revoke_token(payload: dict, db: Session) -> None:
    jti = payload.get("jti")
    expiry = payload.get("exp")

    if not jti or not expiry:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    if is_token_revoked(jti, db):
        return

    expires_at = datetime.fromtimestamp(expiry, timezone.utc).replace(tzinfo=None)

    db.add(RevokedToken(jti=jti, expires_at=expires_at))
    db.commit()


def refresh_access_token(token: str, db: Session) -> dict:
    try:
        payload = decode_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required"
        )

    jti = payload.get("jti")

    if not jti or is_token_revoked(jti, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )

    user_id = int(payload.get("sub"))
    user = db.scalar(select(User).where(User.id == user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    revoke_token(payload, db)

    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id, user.role),
        "token_type": "bearer"
    }
