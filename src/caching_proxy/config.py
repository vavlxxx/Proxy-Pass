from pydantic_settings import BaseSettings


class ProxyConfig(BaseSettings):
    CACHE_DEFAULT_TTL: int = 60
    CACHE_DEFAULT_KEY_EXPIRES_AT: str = "expires_at"
    CACHE_DEFAULT_KEY_VALUE: str = "value"
    CACHE_DEFAULT_PORT: int = 3000


settings = ProxyConfig()
