from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.compose import compose_nbest_with_rules
from whisper_wfst.nbest_acceptor import build_nbest_acceptor, select_lowest_asr_cost
from whisper_wfst.protect import protect_text
from whisper_wfst.trace import CorrectionDecisionTrace
from whisper_wfst.types import CorrectionRule, NBestArtifact


@dataclass(frozen=True)
class CorrectionSafetyConfig:
    domain_gate_enabled: bool
    margin: float


@dataclass(frozen=True)
class SegmentCorrectionContext:
    segment_id: str
    domain_allowed: bool
    is_free_talk: bool


def apply_correction_safely(
    artifact: NBestArtifact,
    rules: list[CorrectionRule],
    config: CorrectionSafetyConfig,
    context: SegmentCorrectionContext,
) -> CorrectionDecisionTrace:
    baseline = select_lowest_asr_cost(build_nbest_acceptor(artifact))
    domain_gate_open = config.domain_gate_enabled and context.domain_allowed
    if not domain_gate_open:
        return _trace(
            context=context,
            decision="skipped",
            source_rank=baseline.rank,
            before=baseline.text,
            after=baseline.text,
            asr_cost=baseline.asr_cost,
            total_cost=baseline.asr_cost,
            correction_cost=0.0,
            rule_ids=[],
            domain_gate_open=False,
            margin=config.margin,
            blocked_reason="domain_gate_closed",
        )

    protected_by_rank = {
        hypothesis.rank: protect_text(hypothesis.normalized_text)
        for hypothesis in artifact.hypotheses
    }
    composition = compose_nbest_with_rules(
        artifact,
        rules,
        protected_text_by_rank=protected_by_rank,
    )

    if not composition.applied_rule_ids:
        return _trace(
            context=context,
            decision="skipped",
            source_rank=composition.selected_rank,
            before=composition.original_text,
            after=composition.original_text,
            asr_cost=composition.asr_cost,
            total_cost=composition.asr_cost,
            correction_cost=0.0,
            rule_ids=[],
            domain_gate_open=True,
            margin=config.margin,
            blocked_reason=_no_rule_reason(composition.fallback_reason),
        )

    cost_increase = composition.total_cost - baseline.asr_cost
    if cost_increase > config.margin:
        return _trace(
            context=context,
            decision="blocked",
            source_rank=baseline.rank,
            before=baseline.text,
            after=baseline.text,
            asr_cost=baseline.asr_cost,
            total_cost=composition.total_cost,
            correction_cost=composition.correction_cost,
            rule_ids=composition.applied_rule_ids,
            domain_gate_open=True,
            margin=config.margin,
            blocked_reason="margin_not_met",
        )

    return _trace(
        context=context,
        decision="applied",
        source_rank=composition.selected_rank,
        before=composition.original_text,
        after=composition.corrected_text,
        asr_cost=composition.asr_cost,
        total_cost=composition.total_cost,
        correction_cost=composition.correction_cost,
        rule_ids=composition.applied_rule_ids,
        domain_gate_open=True,
        margin=config.margin,
        blocked_reason=None,
    )


def _trace(
    *,
    context: SegmentCorrectionContext,
    decision: str,
    source_rank: int,
    before: str,
    after: str,
    asr_cost: float,
    total_cost: float,
    correction_cost: float,
    rule_ids: list[str],
    domain_gate_open: bool,
    margin: float,
    blocked_reason: str | None,
) -> CorrectionDecisionTrace:
    return CorrectionDecisionTrace(
        segment_id=context.segment_id,
        decision=decision,
        source_hypothesis_rank=source_rank,
        before_text=before,
        after_text=after,
        asr_cost=asr_cost,
        corrected_total_cost=total_cost,
        correction_cost=correction_cost,
        applied_rule_ids=rule_ids,
        domain_gate_open=domain_gate_open,
        margin=margin,
        blocked_reason=blocked_reason,
        backend_strategy="phrase_rule_fallback",
    )


def _no_rule_reason(fallback_reason: str | None) -> str:
    if fallback_reason in {None, "no_path"}:
        return "no_rule_applied"
    return fallback_reason


__all__ = [
    "CorrectionSafetyConfig",
    "SegmentCorrectionContext",
    "apply_correction_safely",
]
