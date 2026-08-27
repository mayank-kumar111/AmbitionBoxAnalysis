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
    assert result.updated_companies[0]["company_name"] == "Example Corp"
    assert result.updated_companies[0]["changes"]["company_rating"]["old"] == 4.0
    assert result.updated_companies[0]["changes"]["company_rating"]["new"] == 4.2


def test_incremental_merge_does_not_duplicate_unchanged_company(tmp_path):
    master_path = tmp_path / "master.csv"
    master = frame([["Example", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    master.to_csv(master_path, index=False)

    incoming = frame([["Example", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    merged, result = IncrementalIngestor(master_path).merge(incoming)

    assert result.new_records == 0
    assert result.updated_records == 0
    assert result.unchanged_records == 1
    assert result.collapsed_records == 0
    assert len(merged) == 1


def test_incremental_merge_reports_incoming_duplicate_keys(tmp_path):
    master_path = tmp_path / "master.csv"
    master = frame([["Existing", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    master.to_csv(master_path, index=False)

    incoming = frame([
        ["New Co", 4.0, "IT", None, "Private", 10, "Delhi"],
        ["New Co", 4.1, "IT", None, "Private", 10, "Delhi"],
    ])

    merged, result = IncrementalIngestor(master_path).merge(incoming)

    assert result.incoming_records == 1
    assert result.new_records == 1
    assert result.incoming_duplicate_rows == 1
    assert result.collapsed_records == 1
    assert result.final_records == 2
    assert float(merged.loc[merged["company_name"] == "New Co", "company_rating"].iloc[0]) == 4.1


def test_partial_snapshot_does_not_report_removals(tmp_path):
    master_path = tmp_path / "master.csv"
    master = frame([
        ["Existing A", 4.0, "IT", None, "Private", 10, "Jaipur"],
        ["Existing B", 4.0, "IT", None, "Private", 10, "Delhi"],
    ])
    master.to_csv(master_path, index=False)

    incoming = frame([["Existing A", 4.0, "IT", None, "Private", 10, "Jaipur"]])
    _, result = IncrementalIngestor(master_path).merge(incoming)

    assert result.removed_records == 0
    assert result.removal_scope == "partial"
