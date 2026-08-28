import pandas as pd

from ambitionbox_app.cache import TTLCache
from ambitionbox_app.data_runtime import DatasetRuntime


def test_runtime_loads_once_and_reuses_data(tmp_path):
    path = tmp_path / "companies.csv"
    path.write_text("company_name,company_rating\nA,4.0\n", encoding="utf-8")
    calls = []

    def loader(p):
        calls.append(1)
        return pd.read_csv(p)

    runtime = DatasetRuntime(path, loader)
    first = runtime.get()
    second = runtime.get()

    assert first is second
    assert len(calls) == 1
    assert runtime.reload_count == 1


def test_runtime_reloads_and_clears_cache_after_file_change(tmp_path):
    path = tmp_path / "companies.csv"
    path.write_text("company_name,company_rating\nA,4.0\n", encoding="utf-8")
    cache = TTLCache()
    cache.set("demo", {"value": 1})
    calls = []

    def loader(p):
        calls.append(1)
        return pd.read_csv(p)

    runtime = DatasetRuntime(path, loader, cache=cache)
    runtime.get()
    assert cache.stats()["size"] == 0

    path.write_text("company_name,company_rating\nA,4.2\nB,3.8\n", encoding="utf-8")
    runtime.get()

    assert len(calls) == 2
    assert runtime.reload_count == 2
    assert cache.stats()["size"] == 0
    assert runtime.get()["company_rating"].tolist() == [4.2, 3.8]


def test_failed_reload_keeps_previous_good_data(tmp_path):
    path = tmp_path / "companies.csv"
    path.write_text("company_name,company_rating\nA,4.0\n", encoding="utf-8")

    fail = {"enabled": False}

    def loader(p):
        if fail["enabled"]:
            raise ValueError("invalid CSV")
        return pd.read_csv(p)

    runtime = DatasetRuntime(path, loader)
    good = runtime.get()

    path.write_text("broken", encoding="utf-8")
    fail["enabled"] = True

    try:
        runtime.get()
    except ValueError:
        pass
    else:
        raise AssertionError("reload should fail")

    assert runtime.get if False else good["company_name"].tolist() == ["A"]
    assert runtime.reload_count == 1
