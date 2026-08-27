import pandas as pd

from src.pipeline.runner import load_incoming_directory


def test_load_incoming_directory_combines_csvs(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()

    pd.DataFrame([{"company_name": "A"}]).to_csv(snapshot / "02.csv", index=False)
    pd.DataFrame([{"company_name": "B"}]).to_csv(snapshot / "01.csv", index=False)

    result = load_incoming_directory(snapshot)

    assert result["company_name"].tolist() == ["B", "A"]
