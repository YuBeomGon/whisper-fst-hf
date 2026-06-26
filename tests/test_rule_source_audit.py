from pathlib import Path

from whisper_wfst.rule_io import read_correction_rules_csv
from whisper_wfst.rule_source_audit import (
    audit_rule_sources,
    load_rule_source_jsonl,
    render_rule_source_audit_report,
    write_safe_seed_csv,
)


def test_rule_source_audit_classifies_safe_optional_and_disabled_candidates() -> None:
    records = load_rule_source_jsonl(Path("tests/fixtures/rule_source_candidates.jsonl"))

    audited = audit_rule_sources(records)
    by_rule_id = {rule.rule_id: rule for rule in audited}

    assert by_rule_id["R_SAFE_001"].decision == "safe_seed"
    assert by_rule_id["R_SAFE_001"].candidate_mode == "optional"
    assert by_rule_id["R_LOW_SUPPORT_001"].decision == "review_optional"
    assert by_rule_id["R_FINAL_EVAL_001"].decision == "disabled"
    assert by_rule_id["R_PII_001"].decision == "disabled"
    assert by_rule_id["R_LONG_SPAN_001"].decision == "disabled"


def test_final_eval_and_high_risk_rules_are_excluded_from_safe_seed_csv(
    tmp_path: Path,
) -> None:
    records = load_rule_source_jsonl(Path("tests/fixtures/rule_source_candidates.jsonl"))
    audited = audit_rule_sources(records)
    output = tmp_path / "correction_rules_seed.csv"

    write_safe_seed_csv(audited, output)
    rules = read_correction_rules_csv(output)

    assert [rule.rule_id for rule in rules] == ["R_SAFE_001"]
    assert rules[0].wrong == "손해보혐"
    assert rules[0].right == "손해보험"
    assert rules[0].mode == "optional"
    assert rules[0].source == "aligned_segment:aig_train:2"


def test_rule_source_audit_report_contains_counts_and_provenance() -> None:
    records = load_rule_source_jsonl(Path("tests/fixtures/rule_source_candidates.jsonl"))
    audited = audit_rule_sources(records)

    report = render_rule_source_audit_report(audited)

    assert "Input records: 5" in report
    assert "Safe-only seed rules: 1" in report
    assert "Final eval leakage candidates: 1" in report
    assert "R_FINAL_EVAL_001" in report
    assert "source_wav_final_l.wav" in report
    assert "aligned_segment:aig_train:2" in report


def test_committed_safe_seed_csv_is_valid() -> None:
    rules = read_correction_rules_csv(Path("data/correction_rules_seed.csv"))

    assert [rule.rule_id for rule in rules] == ["R_SAFE_001"]
