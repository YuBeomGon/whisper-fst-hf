import json

from whisper_wfst.safety import (
    CorrectionSafetyConfig,
    SegmentCorrectionContext,
    apply_correction_safely,
)
from whisper_wfst.trace import CorrectionDecisionTrace
from whisper_wfst.types import CorrectionRule, Hypothesis, NBestArtifact


def test_trace_is_json_serializable_and_contains_costs() -> None:
    trace = apply_correction_safely(
        _artifact(),
        [
            CorrectionRule(
                "R1",
                "손해보혐",
                "손해보험",
                "obligatory",
                True,
                100,
                0.1,
                source="test",
            )
        ],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=0.2),
        SegmentCorrectionContext(
            segment_id="seg-trace",
            domain_allowed=True,
            is_free_talk=False,
        ),
    )

    payload = trace.to_dict()
    encoded = json.dumps(payload, ensure_ascii=False)
    decoded = CorrectionDecisionTrace.from_dict(json.loads(encoded))

    assert decoded.source_hypothesis_rank == 1
    assert decoded.before_text == "손해보혐"
    assert decoded.after_text == "손해보험"
    assert decoded.asr_cost == 1.0
    assert decoded.corrected_total_cost == 1.1
    assert decoded.correction_cost == 0.1
    assert decoded.applied_rule_ids == ["R1"]
    assert decoded.backend_strategy == "phrase_rule_fallback"


def test_protected_span_blocks_correction_in_safety_order() -> None:
    artifact = NBestArtifact(
        segment_id="seg-protect",
        model="mock",
        runtime="hf-transformers",
        decode_config={},
        hypotheses=[
            Hypothesis(
                1,
                [1],
                "코드 ABC1234",
                "코드 ABC1234",
                "mock",
                True,
                None,
                None,
                -1.0,
                1.0,
            )
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )

    trace = apply_correction_safely(
        artifact,
        [
            CorrectionRule(
                "R_CODE",
                "ABC1234",
                "ABC9999",
                "obligatory",
                True,
                100,
                0.1,
                source="test",
            )
        ],
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=1.0),
        SegmentCorrectionContext(
            segment_id="seg-protect",
            domain_allowed=True,
            is_free_talk=False,
        ),
    )

    assert trace.decision == "skipped"
    assert trace.after_text == "코드 ABC1234"
    assert trace.blocked_reason == "no_rule_applied"


def _artifact() -> NBestArtifact:
    return NBestArtifact(
        segment_id="seg-trace",
        model="mock",
        runtime="hf-transformers",
        decode_config={},
        hypotheses=[
            Hypothesis(1, [1], "손해보혐", "손해보혐", "mock", True, None, None, -1.0, 1.0)
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )
