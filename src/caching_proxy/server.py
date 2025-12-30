from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

from caching_proxy.cache import cache
from caching_proxy.config import settings
from caching_proxy.utils import clean_headers, make_cache_key


@asynccontextmanager
async def lifespan(app):
    async with httpx.AsyncClient(
        timeout=10,
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        ),
    ) as client:
        app.state.client = client
        yield


app = FastAPI(
    title="Caching Proxy Server",
    lifespan=lifespan,
)


def run_server(args):
    app.state.origin = args.origin.rstrip("/")
    uvicorn.run(
        app=app,
        host=settings.CACHE_DEFAULT_HOST,
        port=args.port,
    )


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def proxy(request: Request, path: str) -> Response:
    origin_url = app.state.origin
    proxy_to_url = f"{origin_url}/{path}"

    request_headers = clean_headers(dict(request.headers))
    body = await request.body()

    cache_key = make_cache_key(request)

    if cache_key:
        cached = cache.getval(cache_key)
        if cached:
            headers = dict(cached["headers"])
            headers["X-Cache"] = "HIT"

            return Response(
                content=cached["body"] if request.method != "HEAD" else b"",
                status_code=cached["status"],
                headers=headers,
            )

    resp = await app.state.client.request(
        method=request.method,
        url=proxy_to_url,
        headers=request_headers,
        params=request.query_params,
        content=body,
    )

    response_headers = clean_headers(dict(resp.headers))

    if cache_key and 200 <= resp.status_code < 300:
        cache.setval(
            cache_key,
            {
                "status": resp.status_code,
                "headers": response_headers,
                "body": resp.content,
            },
            ttl=settings.CACHE_DEFAULT_TTL,
        )
        response_headers["X-Cache"] = "MISS"

    return Response(
        content=resp.content if request.method != "HEAD" else b"",
        status_code=resp.status_code,
        headers=response_headers,
    )
