from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

from src.caching_proxy.config import settings
from src.caching_proxy.logconfig import configurate_logging, get_logger
from src.caching_proxy.management import router as router_management
from src.caching_proxy.middlewares import CacheLoggingMiddleware
from src.caching_proxy.service import ProxyServiceDep
from src.caching_proxy.utils import CachingHelper

logger = get_logger("server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        timeout=settings.HTTPX_TIMEOUT,
        follow_redirects=settings.HTTPX_FOLLOW_REDIRECTS,
        limits=httpx.Limits(
            max_connections=settings.HTTPX_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTPX_MAX_KEEP_ALIVE_CONNECTIONS,
        ),
    ) as client:
        app.state.client = client
        logger.info("Running Proxy Server on %s:%s", settings.CACHE_DEFAULT_HOST, app.state.port)
        logger.info("Requests will be proxied from %s", app.state.origin)
        yield
        logger.info("Shutting down Proxy Server...")


configurate_logging()
app = FastAPI(
    title="Caching Proxy Server",
    description="A caching proxy server for GET and HEAD HTTP requests",
    lifespan=lifespan,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(CacheLoggingMiddleware)


def run_server(args):
    app.state.origin = args.origin.rstrip("/")
    app.state.port = args.port
    app.state.ttl = args.ttl if args.ttl >= 0 else 0
    uvicorn.run(app=app, host=settings.CACHE_DEFAULT_HOST, port=args.port)


app.include_router(router_management)


@app.api_route("/{path:path}", methods=["GET", "HEAD"])
async def proxy(
    path: str,
    request: Request,
    proxy_service: ProxyServiceDep,
) -> Response:
    request_components = CachingHelper.extract_request_components(request)
    cache_key = CachingHelper.make_cache_key(request_components)

    cached_response = proxy_service.get_cached_response(
        request,
        cache_key,
        request.method,
    )
    if cached_response:
        return cached_response

    return await proxy_service.fetch_from_origin(request_components)
