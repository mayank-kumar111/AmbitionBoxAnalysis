import pandas as pd

from scripts.verify_master_dataset import verify_master


def valid_frame():
    return pd.DataFrame([
        {
            "company_name": "A",
            "company_rating": 4.2,
            "industry": "IT",
            "size": "1k-5k Employees",
            "type": "Public",
            "years_old": 10,
            "location": "Jaipur",
        },
        {
            "company_name": "B",
            "company_rating": 3.8,
            "industry": "Finance",
            "size": "501-1k Employees",
            "type": "Startup",
            "years_old": 8,
            "location": "Pune",
        },
    ])


def test_valid_master_dataset(tmp_path):
    path = tmp_path / "companies.csv"
    valid_frame().to_csv(path, index=False)
    report = verify_master(path, minimum_rows=2)
    assert report["valid"] is True
    assert report["rows"] == 2
    assert report["duplicate_keys"] == 0
    assert report["invalid_rating_values"] == 0


def test_duplicate_company_location_is_rejected(tmp_path):
    df = pd.concat([valid_frame(), valid_frame().iloc[[0]]], ignore_index=True)
    path = tmp_path / "companies.csv"
    df.to_csv(path, index=False)
    report = verify_master(path)
    assert report["valid"] is False
    assert report["duplicate_keys"] == 2


def test_invalid_rating_is_rejected(tmp_path):
    df = valid_frame()
    df.loc[0, "company_rating"] = 7
    path = tmp_path / "companies.csv"
    df.to_csv(path, index=False)
    report = verify_master(path)
    assert report["valid"] is False
    assert report["invalid_rating_values"] == 1
