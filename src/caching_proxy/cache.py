import time
from typing import Any, Hashable

from caching_proxy.config import settings


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[Hashable, dict[Hashable, Any]] = {}

    def getval(self, key) -> None | Any:
        entry = self._store.get(key, None)
        if not entry:
            return None

        if entry[settings.CACHE_DEFAULT_KEY_EXPIRES_AT] < time.time():
            del self._store[key]
            return None

        return entry[settings.CACHE_DEFAULT_KEY_VALUE]

    def setval(self, key: Hashable, value: Any, ttl: int) -> None:
        self._store[key] = {
            settings.CACHE_DEFAULT_KEY_VALUE: value,
            settings.CACHE_DEFAULT_KEY_EXPIRES_AT: time.time() + ttl,
        }

    def delval(self, key: Hashable) -> None:
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()


cache = InMemoryCache()
