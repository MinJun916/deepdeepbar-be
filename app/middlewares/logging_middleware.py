import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = round(time.time() - start_time, 4)

        log_kwargs = {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "process_time": process_time,
        }

        if response.status_code >= 500:
            logger.error("request_error", **log_kwargs)
        elif response.status_code >= 400:
            logger.warning("request_warning", **log_kwargs)
        else:
            logger.info("request", **log_kwargs)

        return response
