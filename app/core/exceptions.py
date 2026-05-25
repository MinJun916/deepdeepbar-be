from http import HTTPStatus

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.logger import logger


class AppError(Exception):
    def __init__(self, status_code: int | HTTPStatus, message: str):
        self.status_code = int(status_code)
        self.message = message


async def app_error_handler(
    request: Request,
    exc: AppError,
):
    if exc.status_code >= 500:
        logger.exception(
            "server_error",
            status_code=exc.status_code,
            message=exc.message,
            method=request.method,
            path=request.url.path,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "unhandled_exception",
        method=request.method,
        path=request.url.path,
        error=str(exc),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )
