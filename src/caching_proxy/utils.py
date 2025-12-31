from urllib.parse import parse_qsl, urlencode

from fastapi import Request

from src.caching_proxy.config import settings


class CachingHelper:
    @staticmethod
    def clean_headers(headers: dict) -> dict:
        headers = dict(headers)
        headers.pop("host", None)
        return {k: v for k, v in headers.items() if k.lower() not in settings.HOP_BY_HOP_HEADERS}

    @staticmethod
    def normalize_query_params(query_string: str) -> str:
        if not query_string:
            return ""
        params = parse_qsl(query_string)
        return urlencode(sorted(params))

    @staticmethod
    def extract_request_components(request: Request) -> tuple[str, dict]:
        path = request.url.path.lstrip("/")
        query_params = dict(request.query_params)
        return path, query_params

    @staticmethod
    def make_cache_key(request: Request) -> str:
        path, query_params = CachingHelper.extract_request_components(request)
        normalized_query = CachingHelper.normalize_query_params(request.url.query)
        full_path = f"/{path}"
        if normalized_query:
            full_path += f"?{normalized_query}"

        return f"{request.method} {full_path}"
