import time

import pytest

from src.caching_proxy.cache import InMemoryCache


@pytest.fixture
def cache():
    return InMemoryCache()


def test_set_and_get_value(cache):
    cache.setval("key", "value", ttl=10)
    assert cache.getval("key") == "value"


def test_get_nonexistent_key_returns_none(cache):
    assert cache.getval("missing") is None


def test_expired_key_returns_none_and_is_removed(cache):
    cache.setval("key", "value", ttl=1)
    time.sleep(1.1)
    assert cache.getval("key") is None
    assert "key" not in cache._store


def test_delval_removes_key(cache):
    cache.setval("key", "value", ttl=10)
    cache.delval("key")
    assert cache.getval("key") is None


def test_delval_on_missing_key_does_not_fail(cache):
    cache.delval("missing")
    assert cache.getval("missing") is None


def test_clear_removes_all_keys(cache):
    cache.setval("a", 1, ttl=10)
    cache.setval("b", 2, ttl=10)
    cache.clear()
    assert cache.getval("a") is None
    assert cache.getval("b") is None


def test_overwrite_existing_key(cache):
    cache.setval("key", "value1", ttl=10)
    cache.setval("key", "value2", ttl=10)
    assert cache.getval("key") == "value2"


def test_ttl_is_respected_independently(cache):
    cache.setval("short", "a", ttl=1)
    cache.setval("long", "b", ttl=5)
    time.sleep(1.1)
    assert cache.getval("short") is None
    assert cache.getval("long") == "b"
