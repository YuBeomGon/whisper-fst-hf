from whisper_wfst.safety import (
    CorrectionSafetyConfig,
    SegmentCorrectionContext,
    apply_correction_safely,
)
from whisper_wfst.types import CorrectionRule, Hypothesis, NBestArtifact


def test_small_margin_blocks_cost_increasing_correction() -> None:
    trace = apply_correction_safely(
        _artifact(),
        [_rule(cost=0.2)],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=0.05),
        SegmentCorrectionContext(
            segment_id="seg-margin",
            domain_allowed=True,
            is_free_talk=False,
        ),
    )

    assert trace.decision == "blocked"
    assert trace.blocked_reason == "margin_not_met"
    assert trace.after_text == "손해보혐"


def test_sufficient_margin_allows_correction() -> None:
    trace = apply_correction_safely(
        _artifact(),
        [_rule(cost=0.2)],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=0.25),
        SegmentCorrectionContext(
            segment_id="seg-margin",
            domain_allowed=True,
            is_free_talk=False,
        ),
    )

    assert trace.decision == "applied"
    assert trace.after_text == "손해보험"
    assert trace.applied_rule_ids == ["R_MARGIN"]


def _artifact() -> NBestArtifact:
    return NBestArtifact(
        segment_id="seg-margin",
        model="mock",
        runtime="hf-transformers",
        decode_config={},
        hypotheses=[
            Hypothesis(1, [1], "손해보혐", "손해보혐", "mock", True, None, None, -1.0, 1.0)
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )


def _rule(*, cost: float) -> CorrectionRule:
    return CorrectionRule(
        "R_MARGIN",
        "손해보혐",
        "손해보험",
        "obligatory",
        True,
        100,
        cost,
        source="test",
    )
