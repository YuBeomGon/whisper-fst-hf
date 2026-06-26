from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CalibrationCandidate:
    config_id: str
    lambda_weight: float
    margin: float
    num_beams: int
    num_return_sequences: int
    correction_cost: float
    keep_cost: float
    rule_policy: str
    domain_gate_policy: str
    corrected_cer: float
    domain_term_accuracy: float
    overcorrection_rate: float
    free_talk_overcorrection_rate: float


@dataclass(frozen=True)
class HardGate:
    max_free_talk_overcorrection_rate: float
    max_overcorrection_rate: float
    min_domain_term_accuracy: float


def select_best_config(
    candidates: list[CalibrationCandidate],
    gate: HardGate,
) -> CalibrationCandidate:
    passing = [candidate for candidate in candidates if _passes_gate(candidate, gate)]
    if not passing:
        raise ValueError("no calibration candidate passed hard gates")
    return sorted(
        passing,
        key=lambda candidate: (
            -candidate.domain_term_accuracy,
            candidate.corrected_cer,
            candidate.overcorrection_rate,
            candidate.config_id,
        ),
    )[0]


def render_calibration_report(
    selected: CalibrationCandidate,
    *,
    freeze_paths: list[Path],
) -> str:
    checksum_lines = [
        f"- `{path}` sha256 `{_sha256(path)}`" for path in freeze_paths if path.exists()
    ]
    return "\n".join(
        [
            "# Correction Calibration",
            "",
            f"Chosen config: {selected.config_id}",
            "",
            "## Selected Parameters",
            "",
            f"- lambda: {selected.lambda_weight}",
            f"- margin: {selected.margin}",
            f"- num_beams: {selected.num_beams}",
            f"- num_return_sequences: {selected.num_return_sequences}",
            f"- correction_cost: {selected.correction_cost}",
            f"- keep_cost: {selected.keep_cost}",
            f"- rule_policy: {selected.rule_policy}",
            f"- domain_gate_policy: {selected.domain_gate_policy}",
            "",
            "## Metrics",
            "",
            f"- corrected CER: {selected.corrected_cer:.4f}",
            f"- domain term accuracy: {selected.domain_term_accuracy:.4f}",
            f"- overcorrection rate: {selected.overcorrection_rate:.4f}",
            f"- free-talk overcorrection rate: {selected.free_talk_overcorrection_rate:.4f}",
            "",
            "## Freeze Checksums",
            "",
            *checksum_lines,
            "",
            "Synthetic calibration only. Final eval must use frozen config/rules/artifacts.",
            "",
        ]
    )


def _passes_gate(candidate: CalibrationCandidate, gate: HardGate) -> bool:
    return (
        candidate.free_talk_overcorrection_rate
        <= gate.max_free_talk_overcorrection_rate
        and candidate.overcorrection_rate <= gate.max_overcorrection_rate
        and candidate.domain_term_accuracy >= gate.min_domain_term_accuracy
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "CalibrationCandidate",
    "HardGate",
    "render_calibration_report",
    "select_best_config",
]
