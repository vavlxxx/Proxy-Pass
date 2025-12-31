from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, Response, status

from src.caching_proxy.cache import cache
from src.caching_proxy.logconfig import get_logger
from src.caching_proxy.schemas import CachedData, RequestComponents
from src.caching_proxy.utils import CachingHelper

logger = get_logger("service")


class ProxyService:
    def __init__(self, origin: str, ttl: int, client: httpx.AsyncClient):
        self.origin = origin
        self.ttl = ttl
        self.client = client

    def get_cached_response(self, request: Request, cache_key: str, method: str) -> Response | None:
        cached = cache.getval(cache_key)  # type: ignore
        if not cached:
            return None

        cached: CachedData = CachedData.model_validate(cached)

        if self._is_conditional_request(request, cached.headers):
            return self._build_not_modified_response(cached.headers)

        return self._build_cached_response(
            cached.body,
            cached.status_code,
            cached.headers,
            method,
        )

    async def fetch_from_origin(
        self,
        request_components: RequestComponents,
    ) -> Response:
        target_url = CachingHelper.make_absolute_url(
            self.origin,
            request_components.path,
        )

        try:
            resp = await self.client.request(
                method=request_components.method,
                url=target_url,
                params=request_components.params,
                headers=request_components.headers,
                content=None,
            )
        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout after retries fetching %s! Type: %s. DETAIL: %s",
                target_url,
                exc.__class__.__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Origin server timeout: {target_url}",
            )
        except httpx.HTTPError as exc:
            logger.error(
                "HTTP error fetching %s! Type: %s. DETAIL: %s",
                target_url,
                exc.__class__.__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Proxy error: {exc.__class__.__name__}",
            )

        if resp.status_code in range(status.HTTP_200_OK, status.HTTP_300_MULTIPLE_CHOICES):
            cache_key = CachingHelper.make_cache_key(request_components)
            self._save_to_cache(cache_key, resp)

        cleaned_headers = CachingHelper.clean_headers(dict(resp.headers))
        cleaned_headers["X-Cache"] = "MISS"

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=cleaned_headers,
        )

    def _is_conditional_request(
        self,
        request: Request,
        cached_headers: dict,
    ) -> bool:
        if_none_match = request.headers.get("if-none-match")
        if if_none_match:
            cached_etag = cached_headers.get("etag")
            if cached_etag and if_none_match in [cached_etag, "*"]:
                return True

        if_modified_since = request.headers.get("if-modified-since")
        if if_modified_since:
            last_modified = cached_headers.get("last-modified")
            if last_modified and if_modified_since == last_modified:
                return True

        return False

    def _build_not_modified_response(self, cached_headers: dict) -> Response:
        headers = {
            "X-Cache": "HIT",
            "ETag": cached_headers.get("etag", ""),
            "Last-Modified": cached_headers.get("last-modified", ""),
            "Cache-Control": cached_headers.get("cache-control", ""),
        }
        headers = {k: v for k, v in headers.items() if v}

        return Response(
            content=b"",
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers=headers,
        )

    def _build_cached_response(
        self,
        body: bytes,
        status_code: int,
        headers: dict,
        method: str,
    ) -> Response:
        headers = dict(headers)
        headers["X-Cache"] = "HIT"

        if method == "HEAD":
            headers["Content-Length"] = str(len(body))
            body = b""

        return Response(
            content=body,
            status_code=status_code,
            headers=headers,
        )

    def _save_to_cache(self, cache_key: str, response: httpx.Response) -> None:
        cache.setval(
            cache_key,
            CachedData(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.content,
            ).model_dump(),
            ttl=self.ttl,
        )


def get_proxy_service(request: Request) -> ProxyService:
    return ProxyService(
        origin=request.app.state.origin,
        ttl=request.app.state.ttl,
        client=request.app.state.client,
    )


ProxyServiceDep = Annotated[ProxyService, Depends(get_proxy_service)]
