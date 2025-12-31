from time import perf_counter
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.caching_proxy.logconfig import get_logger

logger = get_logger("middleware")


class CacheLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = perf_counter()
        response = await call_next(request)
        process_time = (perf_counter() - start_time) * 1000
        cache_status = response.headers.get("X-Cache", "N/A")
        logger.info(
            "%-8s %-50s STATUS=%s CACHE=%-4s TIME=%.2fms",
            request.method,
            request.url.path,
            response.status_code,
            cache_status,
            process_time,
        )
        return response
