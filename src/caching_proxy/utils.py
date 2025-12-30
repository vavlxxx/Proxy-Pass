from caching_proxy.config import settings


def clean_headers(headers: dict) -> dict:
    headers.pop("host", None)
    filtered_headers = {k: v for k, v in headers.items() if k.lower() not in settings.HOP_BY_HOP_HEADERS}
    return filtered_headers
