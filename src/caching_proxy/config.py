import httpx
from pydantic_settings import BaseSettings


class ProxyConfig(BaseSettings):
    CACHE_DEFAULT_TTL: int = 60
    CACHE_DEFAULT_KEY_EXPIRES_AT: str = "expires_at"
    CACHE_DEFAULT_KEY_VALUE: str = "value"
    CACHE_DEFAULT_KEY_TTL: str = "ttl"
    CACHE_DEFAULT_PORT: int = 3000
    CACHE_DEFAULT_HOST: str = "localhost"

    HTTPX_TIMEOUT: httpx.Timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=10.0,
    )

    HTTPX_FOLLOW_REDIRECTS: bool = True
    HTTPX_MAX_CONNECTIONS: int = 100
    HTTPX_MAX_KEEP_ALIVE_CONNECTIONS: int = 20
    EXCLUDED_HEADERS: list[str] = ["host", "if-none-match", "if-modified-since"]
    HOP_BY_HOP_HEADERS: set[str] = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    CACHEABLE_METHODS: set[str] = {
        "GET",
        "HEAD",
    }


settings = ProxyConfig()
