from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.offline_pipeline import OfflinePipelinePaths, run_offline_pipeline


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run synthetic offline MVP pipeline.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/offline_mvp"))
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("docs/reports/experiments/offline_mvp_run.md"),
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("docs/reports/experiments/offline_mvp_manifest.json"),
    )
    args = parser.parse_args(argv)

    run_offline_pipeline(
        OfflinePipelinePaths(
            nbest_artifact=Path("tests/fixtures/targetability_artifact.json"),
            targetability_manifest=Path("tests/fixtures/targetability_manifest.json"),
            rules=Path("tests/fixtures/correction_rules.csv"),
            evaluation_manifest=Path("tests/fixtures/evaluation_manifest.json"),
            evaluation_predictions=Path("tests/fixtures/evaluation_predictions.json"),
            output_dir=args.output_dir,
            report_path=args.report_path,
            manifest_path=args.manifest_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
