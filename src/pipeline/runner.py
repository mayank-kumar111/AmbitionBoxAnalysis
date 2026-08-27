"""Reproducible orchestration for AmbitionBox data updates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.ingestion.incremental import IncrementalIngestor, IngestionResult
from src.preprocessing.validator import validate_or_raise


@dataclass(frozen=True)
class PipelineConfig:
    master_path: Path
    incoming_directory: Path
    output_path: Path
    report_path: Path
    apply: bool = False
    full_snapshot: bool = False


@dataclass(frozen=True)
class PipelineResult:
    ingestion: IngestionResult
    output_path: Path
    report_path: Path
    applied: bool


def load_incoming_directory(directory: Path) -> pd.DataFrame:
    """Load all CSV files in a snapshot directory in deterministic order."""
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {directory}")

    frames = [pd.read_csv(path) for path in files]
    return pd.concat(frames, ignore_index=True)


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Run validation and incremental merge, optionally applying the output."""
    incoming = load_incoming_directory(config.incoming_directory)
    validate_or_raise(incoming, check_duplicates=False)

    ingestor = IncrementalIngestor(config.master_path)
    proposed_output = config.output_path
    _, result = ingestor.merge(
        incoming,
        output_path=proposed_output,
        full_snapshot=config.full_snapshot,
    )

    if config.apply:
        config.master_path.parent.mkdir(parents=True, exist_ok=True)
        pd.read_csv(proposed_output).to_csv(config.master_path, index=False)
    else:
        # Keep dry runs from looking like applied changes: the proposed output
        # is useful for inspection, but the master is never touched.
        pass

    config.report_path.parent.mkdir(parents=True, exist_ok=True)
    return PipelineResult(
        ingestion=result,
        output_path=proposed_output,
        report_path=config.report_path,
        applied=config.apply,
    )
