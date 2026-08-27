import pandas as pd

from src.preprocessing.cleaner import clean_dataframe, parse_other_data
from src.preprocessing.validator import validate_dataframe


def test_parse_complete_other_data():
    result = parse_other_data(
        "Pharma, 10k-50k Employees, Public, 72 years old, Ahmedabad +152 more"
    )

    assert result == {
        "industry": "Pharma",
        "size": "10k-50k Employees",
        "type": "Public",
        "years_old": 72,
        "location": "Ahmedabad",
    }


def test_parse_other_locations_suffix():
    result = parse_other_data(
        "IT Services, 1k-5k Employees, Public, 20 years old, Mumbai +392 other locations"
    )

    assert result["location"] == "Mumbai"


def test_parse_missing_type_and_industry():
    result = parse_other_data("Jaipur")

    assert result["industry"] is None
    assert result["size"] is None
    assert result["type"] is None
    assert result["years_old"] is None
    assert result["location"] == "Jaipur"


def test_clean_dataframe_removes_index_and_duplicates():
    raw = pd.DataFrame(
        [
            {
                "Unnamed: 0": 0,
                "company_name": " Example Corp ",
                "company_rating": "4.2",
                "other_data": "IT Services, 1k-5k Employees, Public, 20 years old, Jaipur +10 more",
            },
            {
                "Unnamed: 0": 1,
                "company_name": "Example Corp",
                "company_rating": 4.2,
                "other_data": "IT Services, 1k-5k Employees, Public, 20 years old, Jaipur +10 more",
            },
        ]
    )

    cleaned = clean_dataframe(raw)

    assert len(cleaned) == 1
    assert cleaned.columns.tolist() == [
        "company_name",
        "company_rating",
        "industry",
        "size",
        "type",
        "years_old",
        "location",
    ]
    assert cleaned.iloc[0]["company_name"] == "Example Corp"
    assert cleaned.iloc[0]["years_old"] == 20


def test_validator_rejects_invalid_rating():
    df = pd.DataFrame(
        [{
            "company_name": "Example",
            "company_rating": 6,
            "industry": "IT",
            "size": None,
            "type": None,
            "years_old": 10,
            "location": "Jaipur",
        }]
    )

    errors = validate_dataframe(df)
    assert "company_rating contains values outside 1-5" in errors
