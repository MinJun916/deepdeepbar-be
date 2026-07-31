import time

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from app.constants.status_code import INTERNAL_SERVER_ERROR, UNAUTHORIZED
from app.core.config import settings
from app.core.exceptions import AppError

MAX_INTERACTION_AGE_SECONDS = 300


def verify_discord_interaction_signature(
    body: bytes,
    signature: str | None,
    timestamp: str | None,
) -> None:
    public_key = settings.discord_public_key

    if public_key is None:
        raise AppError(
            status_code=INTERNAL_SERVER_ERROR,
            message="Discord Public Key가 설정되지 않았습니다.",
        )

    if not signature or not timestamp:
        raise AppError(
            status_code=UNAUTHORIZED,
            message="Discord 요청 서명을 확인할 수 없습니다.",
        )

    try:
        requested_at = int(timestamp)
        is_fresh = abs(int(time.time()) - requested_at) <= MAX_INTERACTION_AGE_SECONDS
        if not is_fresh:
            raise ValueError

        verify_key = VerifyKey(bytes.fromhex(public_key.get_secret_value()))
        verify_key.verify(timestamp.encode() + body, bytes.fromhex(signature))
    except (BadSignatureError, TypeError, ValueError):
        raise AppError(
            status_code=UNAUTHORIZED,
            message="유효하지 않은 Discord 요청 서명입니다.",
        ) from None
