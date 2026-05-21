import asyncio

from app.core.security import hash_password
from app.database.connection import AsyncSessionLocal
from app.models.user_model import User, UserRole


async def create_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            email="admin@deepdeepbar.com",
            password_hash=hash_password("deepdeep"),
            name="Admin",
            role=UserRole.admin,
            is_active=True,
        )

        db.add(admin)
        await db.commit()

        print("관리자 계정 생성 완료!")


asyncio.run(create_admin())
