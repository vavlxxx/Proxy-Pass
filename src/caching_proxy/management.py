import asyncio
import os
import signal

from fastapi import APIRouter, Request, Response, status

from src.caching_proxy.cache import cache
from src.caching_proxy.config import settings
from src.caching_proxy.schemas import AppStatus

router = APIRouter(prefix=f"/{settings.ADMIN_API_PREFIX}")


@router.post("/__shutdown")
async def shutdown() -> Response:
    async def delayed_shutdown():
        await asyncio.sleep(1.0)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(delayed_shutdown())

    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.get("/__keys")
async def keys() -> dict:
    return {
        "keys": cache.keys,
    }


@router.post("/__clear")
async def clear_cache() -> Response:
    cache.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/__health")
async def health(request: Request) -> AppStatus:
    app = request.app
    return AppStatus(
        host=settings.CACHE_DEFAULT_HOST,
        port=app.state.port,
        origin=app.state.origin,
        ttl=app.state.ttl,
    )
