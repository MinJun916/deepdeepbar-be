import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(user_id: uuid.UUID, role: str):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "role": role,
        "type": "access",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: uuid.UUID):
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days,
    )

    payload = {
        "sub": str(user_id),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str):
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=settings.jwt_algorithm,
    )
