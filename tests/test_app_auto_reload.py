from pathlib import Path

import pandas as pd


def test_app_reloads_dataset_when_csv_changes(tmp_path, monkeypatch):
    from ambitionbox_app import app as app_module

    path = tmp_path / "companies.csv"
    first = pd.DataFrame([
        {"company_name": "Alpha", "company_rating": 4.0, "industry": "IT",
         "size": "1k-5k Employees", "type": "Public", "years_old": 10, "location": "Jaipur"},
    ])
    second = pd.DataFrame([
        {"company_name": "Alpha", "company_rating": 4.0, "industry": "IT",
         "size": "1k-5k Employees", "type": "Public", "years_old": 10, "location": "Jaipur"},
        {"company_name": "Beta", "company_rating": 3.5, "industry": "Finance",
         "size": "501-1k Employees", "type": "Startup", "years_old": 5, "location": "Pune"},
    ])
    first.to_csv(path, index=False)

    monkeypatch.setattr(app_module, "DATA_PATH", str(path))
    app_module.DATA_RUNTIME = app_module.DatasetRuntime(path, app_module.load_data, app_module.API_CACHE)
    app_module.DF = app_module.DATA_RUNTIME.get()
    app_module.META = app_module.build_meta(app_module.DF)

    client = app_module.app.test_client()
    first_response = client.get("/api/meta")
    assert first_response.status_code == 200
    assert first_response.get_json()["totals"]["companies"] == 1

    second.to_csv(path, index=False)
    # Ensure the filesystem fingerprint differs even on filesystems with coarse mtimes.
    Path(path).touch()

    second_response = client.get("/api/meta")
    assert second_response.status_code == 200
    assert second_response.get_json()["totals"]["companies"] == 2
