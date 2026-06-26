from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PERSONAL_TAGS = {"NAME", "CONTACT", "ADDR"}
SQUARE_TAG_PATTERN = re.compile(r"\[([A-Z_]{2,30})\]")
ANGLE_CORRECTION_PATTERN = re.compile(
    r"<([^<>]{1,120})>\s*(?:/|->|=>)\s*<([^<>]{1,120})>"
)
PROTECTED_ANGLE_PATTERN = re.compile(
    r"<[^<>]{1,120}>\s*\[(?:NAME|CONTACT|ADDR)\]"
)
STANDALONE_ANGLE_PATTERN = re.compile(r"<[^<>]{1,120}>")
INDEX_LINE_PATTERN = re.compile(r"\s*(\d{1,4})\s*")


@dataclass(frozen=True)
class LabelBlock:
    index: int | None
    start_sec: int | None
    end_sec: int | None
    raw_text: str
    normalized_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "start_sec": self.start_sec,
            "end_sec": self.end_sec,
            "raw_text": self.raw_text,
            "normalized_text": self.normalized_text,
        }


@dataclass(frozen=True)
class LabelDocument:
    source_stem: str
    blocks: list[LabelBlock]
    normalized_text: str
    format_flags: list[str]
    exclusion_reasons: list[str]
    square_tag_counts: dict[str, int]
    angle_markup_count: int

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "source_stem": self.source_stem,
            "block_count": len(self.blocks),
            "normalized_text_chars": len(re.sub(r"\s+", "", self.normalized_text)),
            "format_flags": list(self.format_flags),
            "exclusion_reasons": list(self.exclusion_reasons),
            "square_tag_counts": dict(self.square_tag_counts),
            "angle_markup_count": self.angle_markup_count,
        }


@dataclass(frozen=True)
class LabelFormatAudit:
    input_label_count: int
    parsed_label_count: int
    format_flag_counts: dict[str, int]
    exclusion_counts: dict[str, int]
    square_tag_counts: dict[str, int]
    angle_markup_total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_label_count": self.input_label_count,
            "parsed_label_count": self.parsed_label_count,
            "format_flag_counts": dict(self.format_flag_counts),
            "exclusion_counts": dict(self.exclusion_counts),
            "square_tag_counts": dict(self.square_tag_counts),
            "angle_markup_total": self.angle_markup_total,
        }


def normalize_label_text(text: str) -> str:
    normalized = ANGLE_CORRECTION_PATTERN.sub(lambda match: f" {match.group(2)} ", text)
    normalized = PROTECTED_ANGLE_PATTERN.sub(" ", normalized)
    normalized = SQUARE_TAG_PATTERN.sub(" ", normalized)
    normalized = STANDALONE_ANGLE_PATTERN.sub(" ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def parse_label_file(path: Path) -> LabelDocument:
    return parse_label_text(path.read_text(encoding="utf-8", errors="replace"), path.stem)


def parse_label_text(text: str, source_stem: str) -> LabelDocument:
    square_tag_counts = Counter(SQUARE_TAG_PATTERN.findall(text))
    angle_markup_count = len(STANDALONE_ANGLE_PATTERN.findall(text))
    raw_blocks, format_flags = _split_index_blocks(text)

    blocks: list[LabelBlock] = []
    for index, raw_text in raw_blocks:
        normalized_text = normalize_label_text(raw_text)
        blocks.append(
            LabelBlock(
                index=index,
                start_sec=(index - 1) * 30 if index is not None else None,
                end_sec=index * 30 if index is not None else None,
                raw_text=raw_text.strip(),
                normalized_text=normalized_text,
            )
        )

    normalized_document_text = " ".join(block.normalized_text for block in blocks).strip()
    exclusion_reasons = _exclusion_reasons(blocks, normalized_document_text)
    if square_tag_counts["SCRIPT_START"] != square_tag_counts["SCRIPT_END"]:
        format_flags.append("script_tag_unbalanced")

    return LabelDocument(
        source_stem=source_stem,
        blocks=blocks,
        normalized_text=normalized_document_text,
        format_flags=sorted(set(format_flags)),
        exclusion_reasons=exclusion_reasons,
        square_tag_counts=dict(square_tag_counts),
        angle_markup_count=angle_markup_count,
    )


def audit_label_files(root: Path, channel: str = "l") -> LabelFormatAudit:
    docs = [parse_label_file(path) for path in sorted(root.glob(f"*/*_{channel}.txt"))]
    format_flag_counts = Counter(flag for doc in docs for flag in doc.format_flags)
    exclusion_counts = Counter(reason for doc in docs for reason in doc.exclusion_reasons)
    square_tag_counts = Counter()
    for doc in docs:
        square_tag_counts.update(doc.square_tag_counts)
    return LabelFormatAudit(
        input_label_count=len(docs),
        parsed_label_count=len(docs),
        format_flag_counts=dict(format_flag_counts),
        exclusion_counts=dict(exclusion_counts),
        square_tag_counts=dict(square_tag_counts),
        angle_markup_total=sum(doc.angle_markup_count for doc in docs),
    )


def write_label_format_audit_json(audit: LabelFormatAudit, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit.to_dict(), ensure_ascii=False, indent=2) + "\n", "utf-8")


def render_label_format_audit_report(audit: LabelFormatAudit) -> str:
    lines = [
        "# Label Format Audit",
        "",
        "## Summary",
        "",
        f"- Input labels: {audit.input_label_count}",
        f"- Parsed labels: {audit.parsed_label_count}",
        f"- Angle markup count: {audit.angle_markup_total}",
        "",
        "## Format Flags",
        "",
        "| Flag | Count |",
        "| --- | ---: |",
    ]
    lines.extend(_counter_lines(audit.format_flag_counts, "none"))
    lines.extend(
        [
            "",
            "## Exclusion Counts",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(_counter_lines(audit.exclusion_counts, "none"))
    lines.extend(
        [
            "",
            "## Square Tags",
            "",
            "| Tag | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(_counter_lines(audit.square_tag_counts, "none"))
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report contains aggregate parser metadata only.",
            "- Raw transcript text is intentionally omitted.",
            "",
        ]
    )
    return "\n".join(lines)


def _split_index_blocks(text: str) -> tuple[list[tuple[int | None, str]], list[str]]:
    lines = text.splitlines()
    expected_index = 1
    found_index = False
    pre_index_lines: list[str] = []
    current_index: int | None = None
    current_lines: list[str] = []
    blocks: list[tuple[int | None, str]] = []
    flags: list[str] = []

    for line in lines:
        maybe_index = _expected_index(line, expected_index)
        if maybe_index is not None:
            if not found_index:
                found_index = True
                if any(item.strip() for item in pre_index_lines):
                    flags.append("index_not_first")
            elif current_index is not None:
                blocks.append((current_index, "\n".join(current_lines)))
            current_index = maybe_index
            current_lines = pre_index_lines if maybe_index == 1 else []
            pre_index_lines = []
            expected_index += 1
            continue
        if found_index:
            current_lines.append(line)
        else:
            pre_index_lines.append(line)

    if found_index and current_index is not None:
        blocks.append((current_index, "\n".join(current_lines)))
    if not found_index:
        flags.append("no_index_fallback")
        return [(None, text)], flags
    if expected_index <= 2:
        flags.append("single_index_only")
    return blocks, flags


def _expected_index(line: str, expected: int) -> int | None:
    match = INDEX_LINE_PATTERN.fullmatch(line)
    if not match:
        return None
    value = int(match.group(1))
    if value == expected:
        return value
    return None


def _exclusion_reasons(blocks: list[LabelBlock], normalized_text: str) -> list[str]:
    reasons: list[str] = []
    text_chars = len(re.sub(r"\s+", "", normalized_text))
    indexed_block_count = sum(1 for block in blocks if block.index is not None)
    if indexed_block_count <= 2 or text_chars < 120:
        reasons.append("too_short_label")
    return reasons


def _counter_lines(counter: dict[str, int], empty_label: str) -> list[str]:
    if not counter:
        return [f"| {empty_label} | 0 |"]
    return [f"| {key} | {counter[key]} |" for key in sorted(counter)]


__all__ = [
    "LabelBlock",
    "LabelDocument",
    "LabelFormatAudit",
    "audit_label_files",
    "normalize_label_text",
    "parse_label_file",
    "parse_label_text",
    "render_label_format_audit_report",
    "write_label_format_audit_json",
]
