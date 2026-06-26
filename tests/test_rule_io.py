from pathlib import Path

import pytest

from whisper_wfst.rule_io import read_correction_rules_csv, write_correction_rules_csv
from whisper_wfst.types import ContractValidationError, CorrectionRule


def test_correction_rules_roundtrip_csv(tmp_path: Path) -> None:
    rules = [
        CorrectionRule(
            rule_id="R_SAMPLE_001",
            wrong="손해보혐",
            right="손해보험",
            mode="optional",
            enabled=True,
            priority=100,
            cost=1.0,
            source="p3_sample",
        )
    ]
    path = tmp_path / "rules.csv"

    write_correction_rules_csv(rules, path)
    loaded = read_correction_rules_csv(path)

    assert loaded == rules


def test_rule_reader_parses_boolean_values(tmp_path: Path) -> None:
    path = tmp_path / "rules.csv"
    path.write_text(
        "rule_id,wrong,right,mode,enabled,priority,cost,left_context,right_context,source\n"
        "R001,손해보혐,손해보험,optional,false,10,1.25,,,fixture\n",
        encoding="utf-8",
    )

    [rule] = read_correction_rules_csv(path)

    assert rule.enabled is False
    assert rule.cost == 1.25


def test_rule_rejects_reserved_context_fields() -> None:
    with pytest.raises(ContractValidationError, match="left_context"):
        CorrectionRule(
            rule_id="R_BAD_CONTEXT",
            wrong="손해보혐",
            right="손해보험",
            mode="optional",
            enabled=True,
            priority=10,
            cost=1.0,
            left_context="가입",
        )


def test_rule_rejects_invalid_mode_and_cost() -> None:
    with pytest.raises(ContractValidationError, match="mode"):
        CorrectionRule(
            rule_id="R_BAD_MODE",
            wrong="손해보혐",
            right="손해보험",
            mode="maybe",
            enabled=True,
            priority=10,
            cost=1.0,
        )

    with pytest.raises(ContractValidationError, match="cost"):
        CorrectionRule(
            rule_id="R_BAD_COST",
            wrong="손해보혐",
            right="손해보험",
            mode="optional",
            enabled=True,
            priority=10,
            cost=-1.0,
        )


def test_rule_reader_rejects_duplicate_rule_ids(tmp_path: Path) -> None:
    path = tmp_path / "rules.csv"
    path.write_text(
        "rule_id,wrong,right,mode,enabled,priority,cost,left_context,right_context,source\n"
        "R001,손해보혐,손해보험,optional,true,10,1.0,,,fixture\n"
        "R001,보혐,보험,optional,true,20,1.0,,,fixture\n",
        encoding="utf-8",
    )

    with pytest.raises(ContractValidationError, match="duplicate rule_id"):
        read_correction_rules_csv(path)


def test_committed_rule_fixtures_are_valid() -> None:
    fixture_rules = read_correction_rules_csv(Path("tests/fixtures/correction_rules.csv"))
    data_rules = read_correction_rules_csv(Path("data/correction_rules.csv"))

    assert fixture_rules[0].rule_id == "R_SAMPLE_001"
    assert data_rules[0].rule_id == "R_SAMPLE_001"
