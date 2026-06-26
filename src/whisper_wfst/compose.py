from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.correction_wfst import RuleApplicationCandidate, apply_rules_to_text
from whisper_wfst.nbest_acceptor import build_nbest_acceptor, select_lowest_asr_cost
from whisper_wfst.types import CorrectionRule, NBestArtifact


@dataclass(frozen=True)
class CompositionResult:
    selected_rank: int
    original_text: str
    corrected_text: str
    total_cost: float
    asr_cost: float
    correction_cost: float
    applied_rule_ids: list[str]
    backend_strategy: str
    fallback_reason: str | None


def compose_nbest_with_rules(
    artifact: NBestArtifact,
    rules: list[CorrectionRule],
) -> CompositionResult:
    candidates = build_nbest_acceptor(artifact)
    no_rule_fallback = select_lowest_asr_cost(candidates)
    scored: list[CompositionResult] = []

    for candidate in candidates:
        keep_branch = RuleApplicationCandidate(
            text=candidate.text,
            applied_rule_ids=[],
            correction_cost=0.0,
        )
        branches = [keep_branch]
        matching_rules = [rule for rule in rules if rule.enabled and rule.mode != "disabled"]
        if any(
            rule.mode == "obligatory" and rule.wrong in candidate.text
            for rule in matching_rules
        ):
            branches = []
        corrected_branch = apply_rules_to_text(candidate.text, matching_rules)[0]
        if corrected_branch.applied_rule_ids:
            branches.append(corrected_branch)

        for branch in branches:
            scored.append(
                CompositionResult(
                    selected_rank=candidate.rank,
                    original_text=candidate.text,
                    corrected_text=branch.text,
                    total_cost=candidate.asr_cost + branch.correction_cost,
                    asr_cost=candidate.asr_cost,
                    correction_cost=branch.correction_cost,
                    applied_rule_ids=branch.applied_rule_ids,
                    backend_strategy="phrase_rule_fallback",
                    fallback_reason=None,
                )
            )

    if not scored:
        return CompositionResult(
            selected_rank=no_rule_fallback.rank,
            original_text=no_rule_fallback.text,
            corrected_text=no_rule_fallback.text,
            total_cost=no_rule_fallback.asr_cost,
            asr_cost=no_rule_fallback.asr_cost,
            correction_cost=0.0,
            applied_rule_ids=[],
            backend_strategy="phrase_rule_fallback",
            fallback_reason="no_path",
        )

    selected = min(scored, key=lambda result: (result.total_cost, result.selected_rank))
    if not selected.applied_rule_ids:
        return CompositionResult(
            selected_rank=selected.selected_rank,
            original_text=selected.original_text,
            corrected_text=selected.corrected_text,
            total_cost=selected.total_cost,
            asr_cost=selected.asr_cost,
            correction_cost=selected.correction_cost,
            applied_rule_ids=[],
            backend_strategy=selected.backend_strategy,
            fallback_reason="no_rule_applied",
        )
    return selected


__all__ = ["CompositionResult", "compose_nbest_with_rules"]
