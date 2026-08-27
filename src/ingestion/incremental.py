"""Incrementally merge company snapshots and explain every change."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.preprocessing.cleaner import FINAL_COLUMNS
from src.preprocessing.validator import validate_or_raise

KEY_COLUMNS = ["company_name", "location"]
COMPARE_COLUMNS = [column for column in FINAL_COLUMNS if column not in KEY_COLUMNS]


@dataclass(frozen=True)
class IngestionResult:
    previous_records: int
    incoming_records: int
    final_records: int
    new_records: int
    updated_records: int
    unchanged_records: int
    invalid_records: int
    incoming_duplicate_rows: int = 0
    master_duplicate_keys: int = 0
    collapsed_records: int = 0
    removed_records: int = 0
    removal_scope: str = "partial"
    new_companies: tuple[dict[str, Any], ...] = ()
    updated_companies: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IncrementalIngestor:
    """Merge cleaned snapshots using company name + location as identity."""

    def __init__(self, master_path: str | Path) -> None:
        self.master_path = Path(master_path)

    @staticmethod
    def _normalize_key(series: pd.Series) -> pd.Series:
        return (
            series.astype("string")
            .fillna("")
            .str.strip()
            .str.casefold()
            .str.replace(r"\s+", " ", regex=True)
        )

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = set(FINAL_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        prepared = df[FINAL_COLUMNS].copy()
        prepared["company_name"] = prepared["company_name"].astype("string").str.strip()
        prepared["location"] = prepared["location"].astype("string").str.strip()
        prepared["company_rating"] = pd.to_numeric(prepared["company_rating"], errors="coerce")
        prepared["years_old"] = pd.to_numeric(prepared["years_old"], errors="coerce").astype("Int64")
        for column in ["industry", "size", "type"]:
            prepared[column] = prepared[column].astype("string").str.strip()
        return prepared.reset_index(drop=True)

    @staticmethod
    def _detail(row: pd.Series) -> dict[str, Any]:
        return {
            "company_name": None if pd.isna(row["company_name"]) else str(row["company_name"]),
            "location": None if pd.isna(row["location"]) else str(row["location"]),
        }

    def merge(
        self,
        incoming: pd.DataFrame,
        output_path: str | Path | None = None,
        *,
        full_snapshot: bool = False,
    ) -> tuple[pd.DataFrame, IngestionResult]:
        """Merge incoming records and return the merged frame plus audit metrics.

        ``full_snapshot=False`` is the safe default because a partial scrape cannot
        prove that an absent master record was removed from the source.
        """
        if self.master_path.exists():
            master = self._prepare(pd.read_csv(self.master_path))
        else:
            master = pd.DataFrame(columns=FINAL_COLUMNS)

        incoming = self._prepare(incoming)
        previous_records = len(master)
        raw_incoming_records = len(incoming)

        master["_key_name"] = self._normalize_key(master["company_name"])
        master["_key_location"] = self._normalize_key(master["location"])
        incoming["_key_name"] = self._normalize_key(incoming["company_name"])
        incoming["_key_location"] = self._normalize_key(incoming["location"])

        master = master.drop_duplicates(subset=["_key_name", "_key_location"], keep="last")
        master_duplicate_keys = previous_records - len(master)

        incoming_key_before = len(incoming)
        incoming = incoming.drop_duplicates(subset=["_key_name", "_key_location"], keep="last")
        incoming_duplicate_rows = incoming_key_before - len(incoming)
        incoming_records = len(incoming)

        master_index = master.set_index(["_key_name", "_key_location"], drop=False)
        incoming_index = incoming.set_index(["_key_name", "_key_location"], drop=False)

        common_keys = master_index.index.intersection(incoming_index.index)
        new_keys = incoming_index.index.difference(master_index.index)

        updated_keys: list[Any] = []
        for key in common_keys:
            old = master_index.loc[key]
            new = incoming_index.loc[key]
            if any(not _values_equal(old[column], new[column]) for column in COMPARE_COLUMNS):
                updated_keys.append(key)

        updated = incoming_index.loc[updated_keys] if updated_keys else incoming_index.iloc[0:0]
        new_rows = incoming_index.loc[new_keys]

        unchanged_records = len(common_keys) - len(updated_keys)
        merged = master_index.drop(index=updated_keys, errors="ignore")
        merged = pd.concat([merged, updated, new_rows], axis=0)
        merged = merged.reset_index(drop=True)
        merged = merged[FINAL_COLUMNS].drop_duplicates(subset=KEY_COLUMNS, keep="last")
        merged = merged.sort_values(["company_name", "location"], na_position="last").reset_index(drop=True)

        validate_or_raise(merged)

        master_keys = set(master_index.index)
        incoming_keys = set(incoming_index.index)
        removed_keys = master_keys - incoming_keys if full_snapshot else set()

        updated_details: list[dict[str, Any]] = []
        for key in updated_keys:
            old = master_index.loc[key]
            new = incoming_index.loc[key]
            changes = {}
            for column in COMPARE_COLUMNS:
                if not _values_equal(old[column], new[column]):
                    changes[column] = {
                        "old": None if pd.isna(old[column]) else old[column].item() if hasattr(old[column], "item") else old[column],
                        "new": None if pd.isna(new[column]) else new[column].item() if hasattr(new[column], "item") else new[column],
                    }
            detail = self._detail(new)
            detail["changes"] = changes
            updated_details.append(detail)

        new_details = [self._detail(new_rows.loc[key]) for key in new_keys]

        result = IngestionResult(
            previous_records=previous_records,
            incoming_records=incoming_records,
            final_records=len(merged),
            new_records=len(new_rows),
            updated_records=len(updated),
            unchanged_records=unchanged_records,
            invalid_records=0,
            incoming_duplicate_rows=incoming_duplicate_rows,
            master_duplicate_keys=master_duplicate_keys,
            collapsed_records=master_duplicate_keys + incoming_duplicate_rows,
            removed_records=len(removed_keys),
            removal_scope="full" if full_snapshot else "partial",
            new_companies=tuple(new_details),
            updated_companies=tuple(updated_details),
        )

        if output_path is not None:
            destination = Path(output_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            merged.to_csv(destination, index=False)

        return merged, result


def _values_equal(left: object, right: object) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    if pd.isna(left) or pd.isna(right):
        return False
    return str(left).strip() == str(right).strip()
