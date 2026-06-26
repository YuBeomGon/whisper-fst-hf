from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.calibration import (
    CalibrationCandidate,
    HardGate,
    render_calibration_report,
    select_best_config,
)

DEFAULT_OUTPUT = Path("docs/reports/experiments/correction_calibration.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run synthetic correction calibration.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    selected = select_best_config(
        _synthetic_candidates(),
        HardGate(
            max_free_talk_overcorrection_rate=0.0,
            max_overcorrection_rate=0.0,
            min_domain_term_accuracy=0.8,
        ),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_calibration_report(
            selected,
            freeze_paths=[
                Path("configs/correction.yaml"),
                Path("data/correction_rules_seed.csv"),
                Path("docs/reports/experiments/offline_mvp_manifest.json"),
            ],
        ),
        encoding="utf-8",
    )
    return 0


def _synthetic_candidates() -> list[CalibrationCandidate]:
    return [
        CalibrationCandidate(
            config_id="safe_only_margin_025",
            lambda_weight=1.0,
            margin=0.25,
            num_beams=20,
            num_return_sequences=20,
            correction_cost=1.0,
            keep_cost=0.0,
            rule_policy="safe_only",
            domain_gate_policy="script_span_only",
            corrected_cer=0.0,
            domain_term_accuracy=1.0,
            overcorrection_rate=0.0,
            free_talk_overcorrection_rate=0.0,
        ),
        CalibrationCandidate(
            config_id="diagnostic_all",
            lambda_weight=1.0,
            margin=1.0,
            num_beams=20,
            num_return_sequences=20,
            correction_cost=0.5,
            keep_cost=0.0,
            rule_policy="diagnostic_all",
            domain_gate_policy="all",
            corrected_cer=0.0,
            domain_term_accuracy=1.0,
            overcorrection_rate=0.1,
            free_talk_overcorrection_rate=0.1,
        ),
    ]


if __name__ == "__main__":
    raise SystemExit(run())
