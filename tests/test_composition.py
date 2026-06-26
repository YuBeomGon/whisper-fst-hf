from whisper_wfst.compose import compose_nbest_with_rules
from whisper_wfst.types import CorrectionRule, Hypothesis, NBestArtifact


def test_composition_selects_obligatory_corrected_candidate_when_total_cost_wins() -> None:
    result = compose_nbest_with_rules(
        _artifact(top_cost=1.0),
        [_rule("R1", "손해보혐", "손해보험", mode="obligatory", cost=0.1)],
    )

    assert result.corrected_text == "손해보험"
    assert result.applied_rule_ids == ["R1"]
    assert result.selected_rank == 1
    assert result.backend_strategy == "phrase_rule_fallback"


def test_optional_keep_branch_can_win_when_correction_cost_is_high() -> None:
    result = compose_nbest_with_rules(
        _artifact(top_cost=1.0),
        [_rule("R1", "손해보혐", "손해보험", cost=10.0)],
    )

    assert result.corrected_text == "손해보혐"
    assert result.applied_rule_ids == []


def test_obligatory_rule_applies_without_keep_branch() -> None:
    result = compose_nbest_with_rules(
        _artifact(top_cost=1.0),
        [_rule("R1", "손해보혐", "손해보험", mode="obligatory", cost=0.1)],
    )

    assert result.corrected_text == "손해보험"
    assert result.applied_rule_ids == ["R1"]


def test_no_rule_match_falls_back_to_lowest_asr_cost() -> None:
    result = compose_nbest_with_rules(
        _artifact(top_cost=1.0),
        [_rule("R1", "상해보혐", "상해보험", cost=0.1)],
    )

    assert result.corrected_text == "손해보혐"
    assert result.fallback_reason == "no_rule_applied"


def _artifact(*, top_cost: float) -> NBestArtifact:
    return NBestArtifact(
        segment_id="seg-p5",
        model="mock",
        runtime="hf-transformers",
        decode_config={},
        hypotheses=[
            Hypothesis(
                1,
                [1],
                "손해보혐",
                "손해보혐",
                "mock",
                True,
                None,
                None,
                -top_cost,
                top_cost,
            ),
            Hypothesis(2, [2], "손해보험", "손해보험", "mock", True, None, None, -2.0, 2.0),
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )


def _rule(
    rule_id: str,
    wrong: str,
    right: str,
    *,
    mode: str = "optional",
    cost: float = 1.0,
) -> CorrectionRule:
    return CorrectionRule(
        rule_id=rule_id,
        wrong=wrong,
        right=right,
        mode=mode,
        enabled=True,
        priority=100,
        cost=cost,
        source="test",
    )
