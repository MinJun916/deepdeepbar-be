from sqlalchemy import select

from app.models.menu_model import Menu


def get_displayed_menu_query():
    return select(Menu).where(
        Menu.is_display.is_(True),
        Menu.deleted_at.is_(None),
    )


def get_active_menu_query():
    return select(Menu).where(
        Menu.deleted_at.is_(None),
    )
