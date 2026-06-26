from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.evaluate import (
    evaluate_predictions,
    load_evaluation_manifest,
    load_prediction_rows,
    render_evaluation_report,
)

DEFAULT_MANIFEST = Path("tests/fixtures/evaluation_manifest.json")
DEFAULT_PREDICTIONS = Path("tests/fixtures/evaluation_predictions.json")
DEFAULT_OUTPUT = Path("docs/reports/probes/evaluation_baseline.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate correction outputs.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    result = evaluate_predictions(
        load_evaluation_manifest(args.manifest),
        load_prediction_rows(args.predictions),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_evaluation_report(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
