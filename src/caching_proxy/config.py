from pathlib import Path

import httpx
from pydantic_settings import BaseSettings


class ProxyConfig(BaseSettings):
    CACHE_DEFAULT_TTL: int = 60
    CACHE_DEFAULT_PORT: int = 3000
    CACHE_DEFAULT_HOST: str = "localhost"

    ADMIN_API_PREFIX: str = "/__management"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    @property
    def LOG_CONFIG_FILE(self) -> Path:
        return self.BASE_DIR / "logging_config.json"

    @property
    def LOG_DIR(self):
        return self.BASE_DIR / "logs"

    @property
    def LOG_FILE(self):
        return self.LOG_DIR / "proxy.log"

    @property
    def APP_CONFIG_FILE(self) -> Path:
        return self.BASE_DIR / "config.json"

    HTTPX_TIMEOUT: httpx.Timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=10.0,
    )
    HTTPX_HEADERS: dict = {
        "User-Agent": "curl/7.68.0",
        "Accept": "*/*",
    }
    HTTPX_FOLLOW_REDIRECTS: bool = True
    HTTPX_MAX_CONNECTIONS: int = 100
    HTTPX_MAX_KEEP_ALIVE_CONNECTIONS: int = 20

    EXCLUDED_HEADERS: list[str] = [
        "host",
        "if-none-match",
        "if-modified-since",
    ]
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


settings = ProxyConfig()
