import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.status_code import BAD_REQUEST
from app.core.discord_security import verify_discord_interaction_signature
from app.core.exceptions import AppError
from app.database.connection import get_db
from app.services.discord_interaction_service import handle_discord_interaction

router = APIRouter(prefix="/discord", tags=["discord"])

db = Annotated[AsyncSession, Depends(get_db)]
discord_signature = Annotated[
    str | None,
    Header(alias="X-Signature-Ed25519"),
]
discord_timestamp = Annotated[
    str | None,
    Header(alias="X-Signature-Timestamp"),
]


@router.post(
    "/interactions",
    summary="Discord Interaction 처리",
    description="Discord의 서명된 버튼 Interaction 요청을 처리합니다.",
)
async def interact_with_discord(
    request: Request,
    db: db,
    signature: discord_signature = None,
    timestamp: discord_timestamp = None,
):
    body = await request.body()
    verify_discord_interaction_signature(body, signature, timestamp)

    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        raise AppError(
            status_code=BAD_REQUEST,
            message="Discord 요청 본문이 올바르지 않습니다.",
        ) from None

    return await handle_discord_interaction(db, payload)
