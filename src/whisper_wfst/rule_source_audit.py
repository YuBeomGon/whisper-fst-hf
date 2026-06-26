from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from whisper_wfst.rule_io import write_correction_rules_csv
from whisper_wfst.types import ContractValidationError, CorrectionRule

SOURCE_TYPES = {"dictionary_registry", "aligned_segment", "phrase_bias_result"}
SPLITS = {"train", "dev", "final_eval", "unknown"}
DECISIONS = {"safe_seed", "review_optional", "disabled"}


@dataclass(frozen=True)
class RuleSourceRecord:
    rule_id: str
    wrong: str
    right: str
    source_type: str
    provenance: str
    source_wav: str | None
    segment_id: str | None
    split: str
    support_count: int
    is_free_talk: bool
    is_script_span: bool
    contains_number_or_pii: bool
    span_length_chars: int
    domain_term: str

    def __post_init__(self) -> None:
        _require_non_empty_str("rule_id", self.rule_id)
        _require_non_empty_str("wrong", self.wrong)
        _require_non_empty_str("right", self.right)
        if self.source_type not in SOURCE_TYPES:
            raise ContractValidationError(f"source_type must be one of {sorted(SOURCE_TYPES)}")
        _require_non_empty_str("provenance", self.provenance)
        _require_optional_str("source_wav", self.source_wav)
        _require_optional_str("segment_id", self.segment_id)
        if self.split not in SPLITS:
            raise ContractValidationError(f"split must be one of {sorted(SPLITS)}")
        _require_int("support_count", self.support_count, minimum=0)
        _require_bool("is_free_talk", self.is_free_talk)
        _require_bool("is_script_span", self.is_script_span)
        _require_bool("contains_number_or_pii", self.contains_number_or_pii)
        _require_int("span_length_chars", self.span_length_chars, minimum=0)
        _require_str("domain_term", self.domain_term)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleSourceRecord:
        return cls(
            rule_id=data["rule_id"],
            wrong=data["wrong"],
            right=data["right"],
            source_type=data["source_type"],
            provenance=data["provenance"],
            source_wav=data.get("source_wav"),
            segment_id=data.get("segment_id"),
            split=data["split"],
            support_count=data["support_count"],
            is_free_talk=data["is_free_talk"],
            is_script_span=data["is_script_span"],
            contains_number_or_pii=data["contains_number_or_pii"],
            span_length_chars=data["span_length_chars"],
            domain_term=data.get("domain_term", ""),
        )


@dataclass(frozen=True)
class AuditedRule:
    rule_id: str
    wrong: str
    right: str
    source_type: str
    provenance: str
    support_count: int
    source_wav: str | None
    segment_id: str | None
    split: str
    free_talk_risk: str
    decision: str
    candidate_mode: str
    reason: str

    def to_correction_rule(self) -> CorrectionRule:
        if self.decision != "safe_seed":
            raise ContractValidationError("only safe_seed audit rows can become seed rules")
        return CorrectionRule(
            rule_id=self.rule_id,
            wrong=self.wrong,
            right=self.right,
            mode=self.candidate_mode,
            enabled=True,
            priority=100,
            cost=1.0,
            source=self.provenance,
        )


def load_rule_source_jsonl(path: Path) -> list[RuleSourceRecord]:
    records: list[RuleSourceRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise ContractValidationError("JSONL row root must be an object")
            records.append(RuleSourceRecord.from_dict(data))
        except ContractValidationError as exc:
            raise ContractValidationError(f"{path}:{line_number}: {exc}") from exc
        except Exception as exc:
            raise ContractValidationError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
    return records


def audit_rule_sources(records: list[RuleSourceRecord]) -> list[AuditedRule]:
    seen_rule_ids: set[str] = set()
    audited: list[AuditedRule] = []
    for record in records:
        if record.rule_id in seen_rule_ids:
            raise ContractValidationError(f"duplicate rule_id {record.rule_id}")
        seen_rule_ids.add(record.rule_id)
        decision, reason = _decision_for(record)
        audited.append(
            AuditedRule(
                rule_id=record.rule_id,
                wrong=record.wrong,
                right=record.right,
                source_type=record.source_type,
                provenance=record.provenance,
                support_count=record.support_count,
                source_wav=record.source_wav,
                segment_id=record.segment_id,
                split=record.split,
                free_talk_risk=_free_talk_risk_for(record),
                decision=decision,
                candidate_mode="disabled" if decision == "disabled" else "optional",
                reason=reason,
            )
        )
    return audited


def write_safe_seed_csv(audited_rules: list[AuditedRule], path: Path) -> None:
    safe_rules = [
        audited_rule.to_correction_rule()
        for audited_rule in audited_rules
        if audited_rule.decision == "safe_seed"
    ]
    write_correction_rules_csv(safe_rules, path)


def render_rule_source_audit_report(audited_rules: list[AuditedRule]) -> str:
    decision_counts = Counter(rule.decision for rule in audited_rules)
    final_eval_count = sum(1 for rule in audited_rules if rule.split == "final_eval")
    high_risk_disabled_count = sum(
        1
        for rule in audited_rules
        if rule.decision == "disabled" and rule.reason != "final_eval_source"
    )

    lines = [
        "# Rule Source Audit Report",
        "",
        "## Summary",
        "",
        f"- Input records: {len(audited_rules)}",
        f"- Safe-only seed rules: {decision_counts['safe_seed']}",
        f"- Review optional candidates: {decision_counts['review_optional']}",
        f"- Disabled candidates: {decision_counts['disabled']}",
        f"- Final eval leakage candidates: {final_eval_count}",
        f"- High-risk disabled candidates: {high_risk_disabled_count}",
        "",
        "## Rules",
        "",
        "| Rule | Decision | Mode | Support | Split | Source wav | Segment | Risk | "
        "Provenance | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for rule in audited_rules:
        lines.append(
            "| "
            f"`{rule.rule_id}` | {rule.decision} | {rule.candidate_mode} | "
            f"{rule.support_count} | {rule.split} | {rule.source_wav or ''} | "
            f"{rule.segment_id or ''} | {rule.free_talk_risk} | {rule.provenance} | "
            f"{rule.reason} |"
        )
    lines.append("")
    return "\n".join(lines)


def _decision_for(record: RuleSourceRecord) -> tuple[str, str]:
    if record.split == "final_eval":
        return "disabled", "final_eval_source"
    if record.contains_number_or_pii:
        return "disabled", "number_or_pii_surface"
    if record.span_length_chars > 24:
        return "disabled", "long_script_span"
    if record.support_count < 2:
        return "review_optional", "low_support"
    if record.is_free_talk and not record.is_script_span:
        return "review_optional", "free_talk_without_script_gate"
    return "safe_seed", "sufficient_support_domain_span"


def _free_talk_risk_for(record: RuleSourceRecord) -> str:
    if record.is_free_talk and not record.is_script_span:
        return "high"
    if record.is_free_talk:
        return "medium"
    return "low"


def _require_str(name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ContractValidationError(f"{name} must be a string")


def _require_non_empty_str(name: str, value: object) -> None:
    _require_str(name, value)
    if not value:
        raise ContractValidationError(f"{name} must be non-empty")


def _require_optional_str(name: str, value: object) -> None:
    if value is not None:
        _require_str(name, value)


def _require_bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise ContractValidationError(f"{name} must be a bool")


def _require_int(name: str, value: object, *, minimum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContractValidationError(f"{name} must be an int")
    if value < minimum:
        raise ContractValidationError(f"{name} must be >= {minimum}")


__all__ = [
    "AuditedRule",
    "RuleSourceRecord",
    "audit_rule_sources",
    "load_rule_source_jsonl",
    "render_rule_source_audit_report",
    "write_safe_seed_csv",
]
