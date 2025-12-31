from pydantic_settings import BaseSettings


class ProxyConfig(BaseSettings):
    CACHE_DEFAULT_TTL: int = 0
    CACHE_DEFAULT_KEY_EXPIRES_AT: str = "expires_at"
    CACHE_DEFAULT_KEY_VALUE: str = "value"
    CACHE_DEFAULT_KEY_TTL: str = "ttl"
    CACHE_DEFAULT_PORT: int = 3000
    CACHE_DEFAULT_HOST: str = "localhost"

    HTTPX_TIMEOUT: int = 10
    HTTPX_FOLLOW_REDIRECTS: bool = True
    HTTPX_MAX_CONNECTIONS: int = 100
    HTTPX_MAX_KEEP_ALIVE_CONNECTIONS: int = 20

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
