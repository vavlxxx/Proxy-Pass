from pydantic import BaseModel, Field


class RequestComponents(BaseModel):
    headers: dict[str, str]
    params: dict[str, str]
    path: str
    method: str


class DataToCache(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: bytes


class CachedBucket(BaseModel):
    ttl: int = Field(default=0, ge=0)
    expires_at: float | None = Field(default=None, ge=0)
    value: DataToCache


class AppConfig(BaseModel):
    host: str
    port: int


class AppStatus(BaseModel):
    host: str
    port: int
    origin: str
    ttl: int
