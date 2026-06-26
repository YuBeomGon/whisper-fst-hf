from whisper_wfst.correction_wfst import apply_rules_to_text
from whisper_wfst.types import CorrectionRule


def test_leftmost_longest_overlap_uses_ordered_rule() -> None:
    rules = [
        CorrectionRule("R_SHORT", "보혐", "보험", "optional", True, 100, 0.1, source="test"),
        CorrectionRule("R_LONG", "손해보혐", "손해보험", "optional", True, 10, 0.1, source="test"),
    ]

    [candidate] = apply_rules_to_text("손해보혐", rules)

    assert candidate.text == "손해보험"
    assert candidate.applied_rule_ids == ["R_LONG"]
