from pathlib import Path

from whisper_wfst.calibration import (
    CalibrationCandidate,
    HardGate,
    render_calibration_report,
    select_best_config,
)


def test_select_best_config_filters_hard_gate_failures() -> None:
    candidates = [
        _candidate("bad_free_talk", free_talk_overcorrection_rate=0.1),
        _candidate("bad_domain", domain_term_accuracy=0.7),
        _candidate("safe_b", domain_term_accuracy=0.9, corrected_cer=0.05),
        _candidate("safe_a", domain_term_accuracy=0.9, corrected_cer=0.04),
    ]

    selected = select_best_config(
        candidates,
        HardGate(
            max_free_talk_overcorrection_rate=0.0,
            max_overcorrection_rate=0.0,
            min_domain_term_accuracy=0.8,
        ),
    )

    assert selected.config_id == "safe_a"
    assert selected.margin == 0.25
    assert selected.rule_policy == "safe_only"


def test_calibration_report_records_selection_and_freeze_checksums() -> None:
    selected = _candidate("safe_a", domain_term_accuracy=0.9, corrected_cer=0.04)
    report = render_calibration_report(
        selected,
        freeze_paths=[
            Path("configs/correction.yaml"),
            Path("data/correction_rules_seed.csv"),
        ],
    )

    assert "Chosen config: safe_a" in report
    assert "margin: 0.25" in report
    assert "num_beams: 20" in report
    assert "free-talk overcorrection rate: 0.0000" in report
    assert "configs/correction.yaml" in report
    assert "sha256" in report


def _candidate(
    config_id: str,
    *,
    domain_term_accuracy: float = 0.9,
    corrected_cer: float = 0.05,
    free_talk_overcorrection_rate: float = 0.0,
) -> CalibrationCandidate:
    return CalibrationCandidate(
        config_id=config_id,
        lambda_weight=1.0,
        margin=0.25,
        num_beams=20,
        num_return_sequences=20,
        correction_cost=1.0,
        keep_cost=0.0,
        rule_policy="safe_only",
        domain_gate_policy="script_span_only",
        corrected_cer=corrected_cer,
        domain_term_accuracy=domain_term_accuracy,
        overcorrection_rate=0.0,
        free_talk_overcorrection_rate=free_talk_overcorrection_rate,
    )
