import asyncio
import getpass
import os

from sqlalchemy import select

import app.models  # noqa: F401 - SQLAlchemy 모델 전체 등록
from app.core.security import hash_password
from app.database.connection import AsyncSessionLocal
from app.models.user_model import User, UserRole


def require_value(env_name: str, prompt: str, *, secret: bool = False) -> str:
    value = os.getenv(env_name)

    if value is None:
        value = getpass.getpass(prompt) if secret else input(prompt)

    normalized_value = value.strip()

    if not normalized_value:
        raise ValueError(f"{env_name} 값이 필요합니다.")

    return normalized_value


async def create_admin() -> None:
    email = require_value("BOOTSTRAP_ADMIN_EMAIL", "관리자 이메일: ").lower()
    password = require_value(
        "BOOTSTRAP_ADMIN_PASSWORD",
        "관리자 비밀번호: ",
        secret=True,
    )
    name = require_value("BOOTSTRAP_ADMIN_NAME", "관리자 이름: ")

    if len(password) < 12:
        raise ValueError("관리자 비밀번호는 12자 이상이어야 합니다.")

    async with AsyncSessionLocal() as db:
        existing_user = await db.scalar(select(User).where(User.email == email))

        if existing_user is not None:
            raise ValueError("이미 존재하는 이메일입니다.")

        admin = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)

        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        await db.refresh(admin)
        print(f"관리자 계정이 생성되었습니다: {admin.email} ({admin.id})")


def main() -> None:
    try:
        asyncio.run(create_admin())
    except ValueError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
