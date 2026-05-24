from sqlalchemy import select

from app.models.user_model import User


def get_users_query():
    return select(User).where(User.deleted_at.is_(None))
