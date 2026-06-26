from pathlib import Path

from whisper_wfst.artifact_io import read_nbest_artifact
from whisper_wfst.rule_io import read_correction_rules_csv
from whisper_wfst.targetability import (
    compute_targetability,
    edit_distance,
    render_targetability_report,
)


def test_edit_distance_for_cer_and_wer() -> None:
    assert edit_distance(list("손해보혐"), list("손해보험")) == 1
    assert edit_distance("손해보혐 가입".split(), "손해보험 가입".split()) == 1


def test_targetability_metrics_find_nbest_oracle_and_seed_surface() -> None:
    artifact = read_nbest_artifact(Path("tests/fixtures/targetability_artifact.json"))
    rules = read_correction_rules_csv(Path("tests/fixtures/correction_rules.csv"))

    result = compute_targetability(
        artifacts=[artifact],
        references={"target-seg-001": "손해보험 가입"},
        domain_terms={"target-seg-001": ["손해보험"]},
        seed_rules=rules,
    )

    assert result.segment_count == 1
    assert result.average_unique_hypotheses == 2.0
    assert result.average_top1_cer > result.average_nbest_oracle_cer
    assert result.average_nbest_oracle_cer == 0.0
    assert result.domain_term_oracle_accuracy == 1.0
    assert result.reference_surface_in_nbest_ratio == 1.0
    assert result.seed_wrong_surface_in_top1_ratio == 1.0
    assert result.seed_wrong_surface_in_nbest_ratio == 1.0


def test_targetability_report_contains_leakage_policy() -> None:
    artifact = read_nbest_artifact(Path("tests/fixtures/targetability_artifact.json"))
    rules = read_correction_rules_csv(Path("tests/fixtures/correction_rules.csv"))
    result = compute_targetability(
        artifacts=[artifact],
        references={"target-seg-001": "손해보험 가입"},
        domain_terms={"target-seg-001": ["손해보험"]},
        seed_rules=rules,
    )

    report = render_targetability_report(result)

    assert "N-best oracle CER" in report
    assert "Seed wrong surface in top1 ratio" in report
    assert "final eval leakage" in report
