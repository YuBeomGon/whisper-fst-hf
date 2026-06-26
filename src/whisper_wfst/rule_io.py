from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from whisper_wfst.types import ContractValidationError, CorrectionRule

RULE_FIELDNAMES = [
    "rule_id",
    "wrong",
    "right",
    "mode",
    "enabled",
    "priority",
    "cost",
    "left_context",
    "right_context",
    "source",
]


def read_correction_rules_csv(path: Path) -> list[CorrectionRule]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != RULE_FIELDNAMES:
            raise ContractValidationError(
                f"{path}: fieldnames must be {', '.join(RULE_FIELDNAMES)}"
            )
        rules: list[CorrectionRule] = []
        seen_rule_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            try:
                rule = _rule_from_csv_row(row)
            except ContractValidationError as exc:
                raise ContractValidationError(f"{path}:{row_number}: {exc}") from exc
            if rule.rule_id in seen_rule_ids:
                raise ContractValidationError(
                    f"{path}:{row_number}: duplicate rule_id {rule.rule_id}"
                )
            seen_rule_ids.add(rule.rule_id)
            rules.append(rule)
    return rules


def write_correction_rules_csv(rules: Iterable[CorrectionRule], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=RULE_FIELDNAMES)
        writer.writeheader()
        for rule in rules:
            writer.writerow(_rule_to_csv_row(rule))


def _rule_from_csv_row(row: dict[str, str]) -> CorrectionRule:
    return CorrectionRule(
        rule_id=row["rule_id"],
        wrong=row["wrong"],
        right=row["right"],
        mode=row["mode"],
        enabled=_parse_bool(row["enabled"]),
        priority=_parse_int("priority", row["priority"]),
        cost=_parse_float("cost", row["cost"]),
        left_context=row["left_context"],
        right_context=row["right_context"],
        source=row["source"],
    )


def _rule_to_csv_row(rule: CorrectionRule) -> dict[str, str]:
    return {
        "rule_id": rule.rule_id,
        "wrong": rule.wrong,
        "right": rule.right,
        "mode": rule.mode,
        "enabled": "true" if rule.enabled else "false",
        "priority": str(rule.priority),
        "cost": str(rule.cost),
        "left_context": rule.left_context,
        "right_context": rule.right_context,
        "source": rule.source,
    }


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ContractValidationError("enabled must be true or false")


def _parse_int(name: str, value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ContractValidationError(f"{name} must be an int") from exc


def _parse_float(name: str, value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ContractValidationError(f"{name} must be a float") from exc


__all__ = [
    "RULE_FIELDNAMES",
    "read_correction_rules_csv",
    "write_correction_rules_csv",
]
