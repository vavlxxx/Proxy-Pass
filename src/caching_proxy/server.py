from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

from caching_proxy.config import settings
from caching_proxy.utils import clean_headers


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


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy(request: Request, path: str) -> Response:
    origin_url = app.state.origin
    proxy_from_url = f"{origin_url}/{path}"

    request_headers = clean_headers(dict(request.headers))
    body = await request.body()

    resp = await app.state.client.request(
        method=request.method,
        url=proxy_from_url,
        headers=request_headers,
        params=request.query_params,
        content=body,
    )

    response_headers = clean_headers(dict(resp.headers))
    response_headers["X-Cache"] = "MISS"

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
    )
