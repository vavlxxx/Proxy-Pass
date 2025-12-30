from urllib.parse import parse_qsl, urlencode, urlparse

from fastapi import Request
from fastapi.datastructures import Headers

from caching_proxy.config import settings


def clean_headers(headers: dict) -> dict:
    headers.pop("host", None)
    filtered_headers = {k: v for k, v in headers.items() if k.lower() not in settings.HOP_BY_HOP_HEADERS}
    return filtered_headers


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = urlencode(sorted(parse_qsl(parsed.query)))
    return parsed._replace(query=query).geturl()


def extract_vary_headers(headers: Headers) -> tuple:
    return tuple((h, headers.get(h)) for h in settings.VARY_HEADERS if headers.get(h) is not None)


def make_cache_key(request: Request) -> tuple | None:
    if request.method not in settings.CACHEABLE_METHODS:
        return None

    url = normalize_url(str(request.url))
    vary = extract_vary_headers(request.headers)

    return (
        request.method,
        url,
        vary,
    )
