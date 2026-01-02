from pathlib import Path

import httpx
from pydantic_settings import BaseSettings


class ProxyConfig(BaseSettings):
    TTL: int = 60
    PORT: int = 3000
    HOST: str = "localhost"

    API_PREFIX_MANAGEMENT: str = "__management"
    API_PREFIX_HEALTH: str = "__health"
    API_PREFIX_SHUTDOWN: str = "__shutdown"
    API_PREFIX_KEYS: str = "__keys"
    API_PREFIX_CLEAR: str = "__clear"

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

    REQUEST_EXCLUDED_HEADERS: list[str] = [
        "host",
        "connection",
        "keep-alive",
        "proxy-connection",
        "transfer-encoding",
    ]

    RESPONSE_EXCLUDED_HEADERS: list[str] = [
        "connection",
        "keep-alive",
        "proxy-connection",
        "transfer-encoding",
        "content-length",
    ]


settings = ProxyConfig()
