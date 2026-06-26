from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.protect import ProtectedText, is_index_protected
from whisper_wfst.types import CorrectionRule


@dataclass(frozen=True)
class RuleApplicationCandidate:
    text: str
    applied_rule_ids: list[str]
    correction_cost: float


def order_rules(rules: list[CorrectionRule]) -> list[CorrectionRule]:
    enabled_rules = [rule for rule in rules if rule.enabled and rule.mode != "disabled"]
    return sorted(
        enabled_rules,
        key=lambda rule: (-len(rule.wrong), -rule.priority, rule.cost, rule.rule_id),
    )


def apply_rules_to_text(
    text: str,
    rules: list[CorrectionRule],
    *,
    protected_text: ProtectedText | None = None,
    force_optional: bool = False,
) -> list[RuleApplicationCandidate]:
    ordered_rules = order_rules(rules)
    corrected_parts: list[str] = []
    applied_rule_ids: list[str] = []
    correction_cost = 0.0
    cursor = 0

    while cursor < len(text):
        match = _find_rule_at(text, cursor, ordered_rules, protected_text)
        if match is None:
            corrected_parts.append(text[cursor])
            cursor += 1
            continue
        corrected_parts.append(match.right)
        applied_rule_ids.append(match.rule_id)
        correction_cost += match.cost
        cursor += len(match.wrong)

    corrected = RuleApplicationCandidate(
        text="".join(corrected_parts),
        applied_rule_ids=applied_rule_ids,
        correction_cost=correction_cost,
    )
    if force_optional:
        return [corrected]
    return [corrected]


def _find_rule_at(
    text: str,
    index: int,
    rules: list[CorrectionRule],
    protected_text: ProtectedText | None,
) -> CorrectionRule | None:
    for rule in rules:
        if not text.startswith(rule.wrong, index):
            continue
        if protected_text is not None and any(
            is_index_protected(position, protected_text)
            for position in range(index, index + len(rule.wrong))
        ):
            continue
        return rule
    return None


__all__ = ["RuleApplicationCandidate", "apply_rules_to_text", "order_rules"]
