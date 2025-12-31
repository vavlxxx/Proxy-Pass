from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, status

from src.caching_proxy.cache import cache
from src.caching_proxy.config import settings
from src.caching_proxy.logging import configurate_logging, get_logger
from src.caching_proxy.utils import CachingHelper


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger("src")
    async with httpx.AsyncClient(
        timeout=settings.HTTPX_TIMEOUT,
        follow_redirects=settings.HTTPX_FOLLOW_REDIRECTS,
        limits=httpx.Limits(
            max_connections=settings.HTTPX_MAX_CONNECTIONS,
            max_keepalive_connections=settings.HTTPX_MAX_KEEP_ALIVE_CONNECTIONS,
        ),
    ) as client:
        app.state.client = client
        logger.info("Running Caching Proxy Server on %s:%s", settings.CACHE_DEFAULT_HOST, app.state.port)
        logger.info("Requests will be proxied from %s", app.state.origin)
        yield
        logger.info("Shutting down Caching Proxy Server...")


configurate_logging()
app = FastAPI(
    title="Caching Proxy Server",
    description="A caching proxy server for GET and HEAD HTTP requests",
    lifespan=lifespan,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


def run_server(args):
    app.state.origin = args.origin.rstrip("/")
    app.state.port = args.port
    app.state.ttl = args.ttl

    uvicorn.run(app=app, host=settings.CACHE_DEFAULT_HOST, port=args.port, log_config="logging_config.json")


@app.api_route(
    "/{path:path}",
    methods=["GET", "HEAD"],
)
async def proxy(request: Request, path: str) -> Response:
    path, query_params = CachingHelper.extract_request_components(request)

    origin_url = app.state.origin
    target_url = f"{origin_url}/{path}"
    request_headers = CachingHelper.clean_headers(dict(request.headers))
    cache_key = CachingHelper.make_cache_key(request)

    cached = cache.getval(cache_key)
    if cached:
        headers = dict(cached["headers"])
        headers["X-Cache"] = "HIT"

        if request.method == "HEAD":
            headers["Content-Length"] = str(len(cached["body"]))

        return Response(
            content=cached["body"] if request.method != "HEAD" else b"",
            status_code=cached["status"],
            headers=headers,
        )

    try:
        resp = await app.state.client.request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=request_headers,
            content=None,
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            detail=f"Proxy Server error: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )

    response_headers = CachingHelper.clean_headers(dict(resp.headers))

    if resp.status_code in range(200, 300):
        cache.setval(
            cache_key,
            {"status": resp.status_code, "headers": response_headers, "body": resp.content},
            ttl=app.state.ttl,
        )
        response_headers["X-Cache"] = "MISS"

    response_content = resp.content
    if request.method == "HEAD":
        response_content = b""

    return Response(
        content=response_content,
        status_code=resp.status_code,
        headers=response_headers,
    )
