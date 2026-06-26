from whisper_wfst.correction_wfst import apply_rules_to_text, order_rules
from whisper_wfst.protect import protect_text
from whisper_wfst.types import CorrectionRule


def test_applies_domain_phrase_correction() -> None:
    [candidate] = apply_rules_to_text("손해보혐 가입", [_rule("R1", "손해보혐", "손해보험")])

    assert candidate.text == "손해보험 가입"
    assert candidate.applied_rule_ids == ["R1"]


def test_does_not_change_unmatched_surface() -> None:
    [candidate] = apply_rules_to_text("혐오 표현", [_rule("R1", "험", "혐")])

    assert candidate.text == "혐오 표현"
    assert candidate.applied_rule_ids == []


def test_length_mismatch_correction() -> None:
    [candidate] = apply_rules_to_text("보험가입", [_rule("R1", "보험가입", "보험 가입")])

    assert candidate.text == "보험 가입"


def test_disabled_rules_are_skipped() -> None:
    [candidate] = apply_rules_to_text(
        "손해보혐",
        [_rule("R_DISABLED", "손해보혐", "손해보험", mode="disabled")],
    )

    assert candidate.text == "손해보혐"
    assert candidate.applied_rule_ids == []


def test_protected_span_blocks_rule_application() -> None:
    protected = protect_text("증권번호 ABC1234", external_spans=None)
    [candidate] = apply_rules_to_text(
        "증권번호 ABC1234",
        [_rule("R_CODE", "ABC1234", "ABC9999")],
        protected_text=protected,
    )

    assert candidate.text == "증권번호 ABC1234"
    assert candidate.applied_rule_ids == []


def test_order_rules_is_deterministic_for_overlaps() -> None:
    rules = [
        _rule("R_SHORT", "보혐", "보험", priority=100, cost=1.0),
        _rule("R_LONG", "손해보혐", "손해보험", priority=10, cost=1.0),
        _rule("R_TIE_B", "손해보혐", "손해 보험", priority=10, cost=0.5),
        _rule("R_TIE_A", "손해보혐", "손해보험", priority=10, cost=0.5),
    ]

    ordered = order_rules(rules)

    assert [rule.rule_id for rule in ordered] == ["R_TIE_A", "R_TIE_B", "R_LONG", "R_SHORT"]


def _rule(
    rule_id: str,
    wrong: str,
    right: str,
    *,
    mode: str = "optional",
    priority: int = 100,
    cost: float = 1.0,
) -> CorrectionRule:
    return CorrectionRule(
        rule_id=rule_id,
        wrong=wrong,
        right=right,
        mode=mode,
        enabled=True,
        priority=priority,
        cost=cost,
        source="test",
    )
