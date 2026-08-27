import pandas as pd

from src.ingestion.incremental import IncrementalIngestor


COLUMNS = ["company_name", "company_rating", "industry", "size", "type", "years_old", "location"]


def frame(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def test_incremental_merge_adds_new_company_and_updates_existing(tmp_path):
    master_path = tmp_path / "master.csv"
    output_path = tmp_path / "merged.csv"

    master = frame([
        ["Example Corp", 4.0, "IT", "1k-5k Employees", "Private", 20, "Jaipur"],
        ["Old Company", 3.5, "Finance", "201-500 Employees", "Public", 30, "Mumbai"],
    ])
    master.to_csv(master_path, index=False)

    incoming = frame([
        [" Example Corp ", 4.2, "IT", "1k-5k Employees", "Private", 20, "JAIPUR"],
        ["New Company", 4.5, "Pharma", "5k-10k Employees", "Public", 15, "Pune"],
    ])

    merged, result = IncrementalIngestor(master_path).merge(incoming, output_path)

    assert result.previous_records == 2
    assert result.incoming_records == 2
    assert result.new_records == 1
    assert result.updated_records == 1
    assert result.unchanged_records == 0
    assert result.final_records == 3
    assert len(merged) == 3
    assert float(merged.loc[merged["company_name"] == "Example Corp", "company_rating"].iloc[0]) == 4.2


def test_incremental_merge_does_not_duplicate_unchanged_company(tmp_path):
    master_path = tmp_path / "master.csv"
    master = frame([["Example", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    master.to_csv(master_path, index=False)

    incoming = frame([["Example", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    merged, result = IncrementalIngestor(master_path).merge(incoming)

    assert result.new_records == 0
    assert result.updated_records == 0
    assert result.unchanged_records == 1
    assert len(merged) == 1
