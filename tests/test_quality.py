import pandas as pd

from src.preprocessing.quality import profile_dataframe


def test_profile_reports_missing_values_and_duplicates():
    df = pd.DataFrame(
        [
            {
                "company_name": "A",
                "company_rating": 4.2,
                "industry": "IT",
                "size": None,
                "type": "Public",
                "years_old": 10,
                "location": "Jaipur",
            },
            {
                "company_name": "A",
                "company_rating": 4.2,
                "industry": "IT",
                "size": None,
                "type": "Public",
                "years_old": 10,
                "location": "Jaipur",
            },
        ]
    )

    report = profile_dataframe(df)

    assert report["rows"] == 2
    assert report["duplicate_rows"] == 1
    assert report["missing_values"]["size"] == 2
    assert report["quality_status"] == "REVIEW"


def test_profile_detects_invalid_values_and_unknown_type():
    df = pd.DataFrame(
        [{
            "company_name": "A",
            "company_rating": 6,
            "industry": "IT",
            "size": "1k-5k Employees",
            "type": "Unknown Type",
            "years_old": -1,
            "location": "Jaipur",
        }]
    )

    report = profile_dataframe(df)

    assert report["invalid_rating_rows"] == 1
    assert report["invalid_age_rows"] == 1
    assert report["unknown_company_types"] == ["Unknown Type"]
    assert report["quality_status"] == "REVIEW"
