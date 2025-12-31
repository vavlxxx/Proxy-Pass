from urllib.parse import urlencode, urljoin

from fastapi import Request

from src.caching_proxy.config import settings
from src.caching_proxy.schemas import RequestComponents


class CachingHelper:
    @staticmethod
    def extract_request_components(request: Request) -> RequestComponents:
        return RequestComponents(
            headers=CachingHelper.clean_headers(dict(request.headers)),
            params=dict(request.query_params),
            path=request.url.path.lstrip("/"),
            method=request.method,
        )

    @staticmethod
    def clean_headers(headers: dict) -> dict:
        headers = dict(headers)

        for header in settings.EXCLUDED_HEADERS:
            headers.pop(header, None)

        return {k: v for k, v in headers.items() if k.lower() not in settings.HOP_BY_HOP_HEADERS}

    @staticmethod
    def make_cache_key(request_components: RequestComponents) -> str:
        path_with_params = request_components.path

        if request_components.params:
            query_string = urlencode(sorted(request_components.params.items()))
            path_with_params = f"{path_with_params}?{query_string}"

        return f"{request_components.method} {path_with_params}"

    @staticmethod
    def make_absolute_url(base: str, path: str) -> str:
        return urljoin(base, path).rstrip("/")
