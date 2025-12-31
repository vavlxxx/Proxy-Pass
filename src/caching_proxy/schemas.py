from pydantic import BaseModel


class RequestComponents(BaseModel):
    headers: dict[str, str]
    params: dict[str, str]
    path: str
    method: str


class CachedData(BaseModel):
    status_code: int
    headers: dict[str, str]
    body: bytes
