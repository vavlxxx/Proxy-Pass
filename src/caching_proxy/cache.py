import time
from typing import Any, Hashable

from src.caching_proxy.config import settings


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[Hashable, dict[Hashable, Any]] = {}

    def getval(self, key) -> None | Any:
        entry = self._store.get(key, None)
        if not entry:
            return None

        ttl = entry[settings.CACHE_DEFAULT_KEY_TTL]
        if ttl > 0 and entry[settings.CACHE_DEFAULT_KEY_EXPIRES_AT] < time.time():
            del self._store[key]
            return None

        return entry[settings.CACHE_DEFAULT_KEY_VALUE]

    def setval(self, key: Hashable, value: Any, ttl: int) -> None:
        if ttl < 0:
            ttl = 0

        self._store[key] = {
            settings.CACHE_DEFAULT_KEY_VALUE: value,
            settings.CACHE_DEFAULT_KEY_EXPIRES_AT: time.time() + ttl,
            settings.CACHE_DEFAULT_KEY_TTL: ttl,
        }

    def delval(self, key: Hashable) -> None:
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()


cache = InMemoryCache()
