from whisper_wfst.safety import (
    CorrectionSafetyConfig,
    SegmentCorrectionContext,
    apply_correction_safely,
)
from whisper_wfst.types import CorrectionRule, Hypothesis, NBestArtifact


def test_domain_gate_off_blocks_optional_correction() -> None:
    trace = apply_correction_safely(
        _artifact(),
        [_rule("R1", "손해보혐", "손해보험")],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=1.0),
        SegmentCorrectionContext(
            segment_id="seg-gate",
            domain_allowed=False,
            is_free_talk=True,
        ),
    )

    assert trace.decision == "skipped"
    assert trace.after_text == "손해보혐"
    assert trace.applied_rule_ids == []
    assert trace.blocked_reason == "domain_gate_closed"


def test_domain_gate_off_blocks_obligatory_correction() -> None:
    trace = apply_correction_safely(
        _artifact(),
        [_rule("R1", "손해보혐", "손해보험", mode="obligatory")],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=1.0),
        SegmentCorrectionContext(
            segment_id="seg-gate",
            domain_allowed=False,
            is_free_talk=False,
        ),
    )

    assert trace.decision == "skipped"
    assert trace.after_text == "손해보혐"
    assert trace.applied_rule_ids == []


def _artifact() -> NBestArtifact:
    return NBestArtifact(
        segment_id="seg-gate",
        model="mock",
        runtime="hf-transformers",
        decode_config={},
        hypotheses=[
            Hypothesis(1, [1], "손해보혐", "손해보혐", "mock", True, None, None, -1.0, 1.0)
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )


def _rule(
    rule_id: str,
    wrong: str,
    right: str,
    *,
    mode: str = "optional",
) -> CorrectionRule:
    return CorrectionRule(rule_id, wrong, right, mode, True, 100, 0.1, source="test")
