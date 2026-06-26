from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from whisper_wfst.rule_io import write_correction_rules_csv
from whisper_wfst.source_inventory import assign_split
from whisper_wfst.types import CorrectionRule

ALLOWED_SEED_SPLITS = {"rule_mining", "dev_review"}
EVAL_SPLIT = "eval_holdout"
RISK_REJECT_FLAGS = {
    "protected_span",
    "contains_number_or_pii",
    "pii_surface",
    "low_alignment_confidence",
}
DIGIT_PATTERN = re.compile(r"\d")
CANONICAL_SURFACE_PATTERN = re.compile(r"[^0-9A-Za-z가-힣]+")
SAFE_SINGLE_TOKEN_PATTERN = re.compile(r"^[0-9A-Za-z가-힣]+$")

PAIR_CANDIDATE_FIELDNAMES = [
    "pair_id",
    "wrong",
    "right",
    "normalized_wrong",
    "normalized_right",
    "support_run_count",
    "support_file_count",
    "support_batch_count",
    "support_variant_count",
    "source_files",
    "source_runs",
    "alignment_confidence",
    "risk_flags",
    "suggested_class",
]

PAIR_REVIEW_FIELDNAMES = [
    "pair_id",
    "review_class",
    "reason",
    "mode",
    "support_run_count",
    "support_file_count",
    "support_batch_count",
    "allowed_file_support",
    "eval_holdout_file_support",
    "source_splits",
    "risk_flags",
    "alignment_confidence",
]


@dataclass(frozen=True)
class PairReviewConfig:
    min_allowed_file_support: int = 3
    min_confidence: float = 0.6
    max_surface_chars: int = 24
    max_auto_seed_length_delta: int = 2
    obligatory_min_file_support: int = 4
    obligatory_min_batch_support: int = 2
    obligatory_min_confidence: float = 0.9


@dataclass(frozen=True)
class PairReviewCandidate:
    pair_id: str
    wrong: str
    right: str
    normalized_wrong: str
    normalized_right: str
    support_run_count: int
    support_file_count: int
    support_batch_count: int
    support_variant_count: int
    source_files: list[str]
    source_runs: list[str]
    alignment_confidence: float
    risk_flags: list[str]
    suggested_class: str

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> PairReviewCandidate:
        return cls(
            pair_id=row["pair_id"],
            wrong=row["wrong"],
            right=row["right"],
            normalized_wrong=row["normalized_wrong"],
            normalized_right=row["normalized_right"],
            support_run_count=_parse_int(row["support_run_count"]),
            support_file_count=_parse_int(row["support_file_count"]),
            support_batch_count=_parse_int(row["support_batch_count"]),
            support_variant_count=_parse_int(row.get("support_variant_count", "0")),
            source_files=_parse_list(row["source_files"]),
            source_runs=_parse_list(row["source_runs"]),
            alignment_confidence=_parse_float(row["alignment_confidence"]),
            risk_flags=_parse_list(row.get("risk_flags", "")),
            suggested_class=row.get("suggested_class", ""),
        )


@dataclass(frozen=True)
class PairReviewRow:
    candidate: PairReviewCandidate
    review_class: str
    reason: str
    mode: str
    source_splits: list[str]
    allowed_source_files: list[str]
    eval_holdout_source_files: list[str]

    def to_correction_rule(self) -> CorrectionRule:
        return CorrectionRule(
            rule_id=f"P18_{self.candidate.pair_id}",
            wrong=self.candidate.normalized_wrong,
            right=self.candidate.normalized_right,
            mode=self.mode,
            enabled=True,
            priority=100,
            cost=1.0,
            source=(
                f"pair_mining_v2:{self.candidate.pair_id}:"
                f"allowed_files={len(self.allowed_source_files)}:"
                f"runs={self.candidate.support_run_count}:"
                f"splits={','.join(self.source_splits)}"
            ),
        )

    def to_redacted_csv_row(self) -> dict[str, str]:
        return {
            "pair_id": self.candidate.pair_id,
            "review_class": self.review_class,
            "reason": self.reason,
            "mode": self.mode,
            "support_run_count": str(self.candidate.support_run_count),
            "support_file_count": str(self.candidate.support_file_count),
            "support_batch_count": str(self.candidate.support_batch_count),
            "allowed_file_support": str(len(self.allowed_source_files)),
            "eval_holdout_file_support": str(len(self.eval_holdout_source_files)),
            "source_splits": ";".join(self.source_splits),
            "risk_flags": ";".join(self.candidate.risk_flags),
            "alignment_confidence": f"{self.candidate.alignment_confidence:.4f}",
        }


@dataclass(frozen=True)
class PairReviewResult:
    rows: list[PairReviewRow]
    seed_rules: list[CorrectionRule]


def read_pair_candidates_csv(path: Path) -> list[PairReviewCandidate]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        missing = [field for field in PAIR_CANDIDATE_FIELDNAMES if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"{path}: missing candidate fields: {', '.join(missing)}")
        return [PairReviewCandidate.from_csv_row(row) for row in reader]


def audit_pair_candidates(
    candidates: list[PairReviewCandidate],
    split_by_source: dict[str, str],
    config: PairReviewConfig | None = None,
) -> PairReviewResult:
    config = config or PairReviewConfig()
    rows = [
        _audit_candidate(candidate, split_by_source, config)
        for candidate in candidates
    ]
    seed_rules = [
        row.to_correction_rule()
        for row in rows
        if row.review_class in {"optional", "obligatory"}
    ]
    return PairReviewResult(rows=rows, seed_rules=seed_rules)


def load_split_manifest(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: split manifest root must be an object")
    split_by_source: dict[str, str] = {}
    for source_stem, metadata in data.items():
        if isinstance(metadata, dict) and isinstance(metadata.get("split"), str):
            split_by_source[source_stem] = metadata["split"]
    return split_by_source


def derive_split_by_source(candidates: list[PairReviewCandidate]) -> dict[str, str]:
    source_files = {
        source_file
        for candidate in candidates
        for source_file in candidate.source_files
        if source_file
    }
    return {source_file: assign_split(source_file) for source_file in sorted(source_files)}


def write_seed_rules_csv(result: PairReviewResult, path: Path) -> None:
    write_correction_rules_csv(result.seed_rules, path)


def write_pair_review_csv(result: PairReviewResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=PAIR_REVIEW_FIELDNAMES)
        writer.writeheader()
        for row in result.rows:
            writer.writerow(row.to_redacted_csv_row())


def render_pair_rule_source_audit_report(result: PairReviewResult) -> str:
    review_counts = Counter(row.review_class for row in result.rows)
    reason_counts = Counter(row.reason for row in result.rows)
    split_counts = Counter(
        split
        for row in result.rows
        for split in row.source_splits
    )
    seed_optional_count = sum(1 for rule in result.seed_rules if rule.mode == "optional")
    seed_obligatory_count = sum(1 for rule in result.seed_rules if rule.mode == "obligatory")

    lines = [
        "# Pair Rule Source Audit v2",
        "",
        "## Summary",
        "",
        f"- Input candidates: {len(result.rows)}",
        f"- Seed optional rules: {seed_optional_count}",
        f"- Seed obligatory rules: {seed_obligatory_count}",
        f"- Needs review candidates: {review_counts['needs_review']}",
        f"- Rejected candidates: {review_counts['reject']}",
        "",
        "## Reason Counts",
        "",
        "| Reason | Count |",
        "| --- | ---: |",
    ]
    if reason_counts:
        for reason, count in sorted(reason_counts.items()):
            lines.append(f"| {reason} | {count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Split Counts",
            "",
            "| Split | Candidate references |",
            "| --- | ---: |",
        ]
    )
    if split_counts:
        for split, count in sorted(split_counts.items()):
            lines.append(f"| {split} | {count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report intentionally omits actual wrong/right surfaces.",
            "- Full review CSV and seed rule CSV are local ignored artifacts.",
            "- Seed rules require downstream correction evaluation before production use.",
        ]
    )
    if not result.seed_rules:
        lines.append("- No candidate passed the conservative automatic seed promotion policy.")
    lines.append("")
    return "\n".join(lines)


def _audit_candidate(
    candidate: PairReviewCandidate,
    split_by_source: dict[str, str],
    config: PairReviewConfig,
) -> PairReviewRow:
    split_pairs = [
        (source_file, split_by_source.get(source_file, "unknown"))
        for source_file in candidate.source_files
    ]
    source_splits = sorted({split for _, split in split_pairs})
    allowed_source_files = sorted(
        source_file for source_file, split in split_pairs if split in ALLOWED_SEED_SPLITS
    )
    eval_holdout_source_files = sorted(
        source_file for source_file, split in split_pairs if split == EVAL_SPLIT
    )

    review_class, reason, mode = _decision_for(
        candidate,
        allowed_source_files=allowed_source_files,
        eval_holdout_source_files=eval_holdout_source_files,
        source_splits=source_splits,
        config=config,
    )
    return PairReviewRow(
        candidate=candidate,
        review_class=review_class,
        reason=reason,
        mode=mode,
        source_splits=source_splits,
        allowed_source_files=allowed_source_files,
        eval_holdout_source_files=eval_holdout_source_files,
    )


def _decision_for(
    candidate: PairReviewCandidate,
    *,
    allowed_source_files: list[str],
    eval_holdout_source_files: list[str],
    source_splits: list[str],
    config: PairReviewConfig,
) -> tuple[str, str, str]:
    risk_flags = set(candidate.risk_flags)
    if risk_flags.intersection({"protected_span", "contains_number_or_pii", "pii_surface"}):
        return "reject", "protected_or_pii_surface", "disabled"
    if DIGIT_PATTERN.search(candidate.normalized_wrong) or DIGIT_PATTERN.search(
        candidate.normalized_right
    ):
        return "reject", "protected_or_pii_surface", "disabled"
    if _canonical_surface(candidate.normalized_wrong) == _canonical_surface(
        candidate.normalized_right
    ):
        return "reject", "format_only_change", "disabled"
    unsafe_shape_reason = _unsafe_rewrite_shape_reason(candidate, config)
    if unsafe_shape_reason:
        return "reject", unsafe_shape_reason, "disabled"
    if (
        len(candidate.normalized_wrong) > config.max_surface_chars
        or len(candidate.normalized_right) > config.max_surface_chars
    ):
        return "reject", "long_surface", "disabled"
    if "low_alignment_confidence" in risk_flags:
        return "reject", "low_alignment_confidence", "disabled"
    if candidate.alignment_confidence < config.min_confidence:
        return "reject", "low_alignment_confidence", "disabled"
    if not allowed_source_files and eval_holdout_source_files:
        return "reject", "eval_holdout_only", "disabled"
    if not allowed_source_files or "unknown" in source_splits:
        return "needs_review", "unknown_source_split", "disabled"
    if len(allowed_source_files) < config.min_allowed_file_support:
        return "needs_review", "low_allowed_file_support", "disabled"
    if (
        len(allowed_source_files) >= config.obligatory_min_file_support
        and candidate.support_batch_count >= config.obligatory_min_batch_support
        and candidate.alignment_confidence >= config.obligatory_min_confidence
    ):
        return "obligatory", "high_support_high_confidence", "obligatory"
    return "optional", "sufficient_allowed_support", "optional"


def _parse_list(value: str) -> list[str]:
    return [item for item in (part.strip() for part in value.split(";")) if item]


def _parse_int(value: str) -> int:
    return int(value)


def _parse_float(value: str) -> float:
    return float(value)


def _canonical_surface(value: str) -> str:
    return CANONICAL_SURFACE_PATTERN.sub("", value)


def _unsafe_rewrite_shape_reason(
    candidate: PairReviewCandidate,
    config: PairReviewConfig,
) -> str | None:
    wrong = candidate.normalized_wrong.strip()
    right = candidate.normalized_right.strip()
    if len(wrong.split()) != 1 or len(right.split()) != 1:
        return "multi_token_or_spacing_change"
    if not SAFE_SINGLE_TOKEN_PATTERN.fullmatch(wrong) or not SAFE_SINGLE_TOKEN_PATTERN.fullmatch(
        right
    ):
        return "punctuation_surface"
    canonical_wrong = _canonical_surface(wrong)
    canonical_right = _canonical_surface(right)
    if canonical_wrong.startswith(canonical_right) or canonical_right.startswith(canonical_wrong):
        return "affix_only_change"
    if abs(len(canonical_wrong) - len(canonical_right)) > config.max_auto_seed_length_delta:
        return "large_length_delta"
    return None


__all__ = [
    "PAIR_REVIEW_FIELDNAMES",
    "PairReviewCandidate",
    "PairReviewConfig",
    "PairReviewResult",
    "PairReviewRow",
    "audit_pair_candidates",
    "derive_split_by_source",
    "load_split_manifest",
    "read_pair_candidates_csv",
    "render_pair_rule_source_audit_report",
    "write_pair_review_csv",
    "write_seed_rules_csv",
]
