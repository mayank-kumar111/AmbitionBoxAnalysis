from ambitionbox_app.cache import TTLCache, make_cache_key


def test_cache_hit_and_clear():
    cache = TTLCache(maxsize=2, ttl_seconds=10)
    cache.set("a", {"value": 1})
    assert cache.get("a") == {"value": 1}
    cache.clear()
    assert cache.get("a") is None


def test_cache_evicts_oldest_entry():
    cache = TTLCache(maxsize=2, ttl_seconds=10)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_cache_key():
    assert make_cache_key("analytics", "industry=IT") == "analytics:industry=IT"
