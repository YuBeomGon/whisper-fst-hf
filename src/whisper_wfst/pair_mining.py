from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from whisper_wfst.label_parser import LabelBlock, parse_label_file

TIMESTAMP_PATTERN = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2},\d{3})"
)
HANGUL_PATTERN = re.compile(r"[가-힣]")


@dataclass(frozen=True)
class PairOccurrence:
    wrong: str
    right: str
    source_stem: str
    run_id: str
    variant: str
    batch: str
    alignment_confidence: float

    def key(self) -> tuple[str, str]:
        return normalize_pair_surface(self.wrong), normalize_pair_surface(self.right)

    def to_dict(self) -> dict[str, Any]:
        return {
            "wrong": self.wrong,
            "right": self.right,
            "source_stem": self.source_stem,
            "run_id": self.run_id,
            "variant": self.variant,
            "batch": self.batch,
            "alignment_confidence": self.alignment_confidence,
        }


@dataclass(frozen=True)
class PairCandidate:
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "wrong": self.wrong,
            "right": self.right,
            "normalized_wrong": self.normalized_wrong,
            "normalized_right": self.normalized_right,
            "support_run_count": self.support_run_count,
            "support_file_count": self.support_file_count,
            "support_batch_count": self.support_batch_count,
            "support_variant_count": self.support_variant_count,
            "source_files": list(self.source_files),
            "source_runs": list(self.source_runs),
            "alignment_confidence": self.alignment_confidence,
            "risk_flags": list(self.risk_flags),
            "suggested_class": self.suggested_class,
        }


@dataclass(frozen=True)
class PairMiningResult:
    candidates: list[PairCandidate]
    occurrence_count: int
    srt_files_scanned: int
    invalid_srt_count: int
    label_count: int


@dataclass(frozen=True)
class SrtTextBlock:
    start_sec: float
    end_sec: float
    text: str

    @property
    def midpoint_sec(self) -> float:
        return (self.start_sec + self.end_sec) / 2


def normalize_pair_surface(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pair_occurrences(
    hyp_text: str,
    ref_text: str,
    source_stem: str,
    run_id: str,
    variant: str,
    batch: str,
) -> list[PairOccurrence]:
    hyp = normalize_pair_surface(hyp_text)
    ref = normalize_pair_surface(ref_text)
    matcher = SequenceMatcher(None, hyp, ref, autojunk=False)
    confidence = round(matcher.ratio(), 4)
    occurrences: list[PairOccurrence] = []
    seen: set[tuple[str, str]] = set()
    for tag, hyp_start, hyp_end, ref_start, ref_end in matcher.get_opcodes():
        if tag == "equal":
            continue
        wrong_start, wrong_end = _expand_to_token_boundary(hyp, hyp_start, hyp_end)
        right_start, right_end = _expand_to_token_boundary(ref, ref_start, ref_end)
        wrong = normalize_pair_surface(hyp[wrong_start:wrong_end])
        right = normalize_pair_surface(ref[right_start:right_end])
        if not _is_valid_pair(wrong, right):
            continue
        key = (wrong, right)
        if key in seen:
            continue
        seen.add(key)
        occurrences.append(
            PairOccurrence(
                wrong=wrong,
                right=right,
                source_stem=source_stem,
                run_id=run_id,
                variant=variant,
                batch=batch,
                alignment_confidence=confidence,
            )
        )
    return occurrences


def aggregate_pair_occurrences(occurrences: list[PairOccurrence]) -> list[PairCandidate]:
    grouped: dict[tuple[str, str], list[PairOccurrence]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[occurrence.key()].append(occurrence)

    candidates: list[PairCandidate] = []
    for index, ((normalized_wrong, normalized_right), group) in enumerate(
        sorted(grouped.items()),
        start=1,
    ):
        first = group[0]
        source_files = sorted({item.source_stem for item in group})
        source_runs = sorted({item.run_id for item in group})
        batches = {item.batch for item in group}
        variants = {item.variant for item in group}
        confidence = round(sum(item.alignment_confidence for item in group) / len(group), 4)
        risk_flags = _risk_flags_for(source_files, confidence)
        candidates.append(
            PairCandidate(
                pair_id=f"P17_{index:06d}",
                wrong=first.wrong,
                right=first.right,
                normalized_wrong=normalized_wrong,
                normalized_right=normalized_right,
                support_run_count=len(source_runs),
                support_file_count=len(source_files),
                support_batch_count=len(batches),
                support_variant_count=len(variants),
                source_files=source_files,
                source_runs=source_runs,
                alignment_confidence=confidence,
                risk_flags=risk_flags,
                suggested_class="needs_review" if risk_flags else "candidate",
            )
        )
    return candidates


def mine_pair_candidates(
    srt_root: Path,
    annotations_root: Path,
    channel: str = "l",
    tolerance_sec: float = 5.0,
) -> PairMiningResult:
    label_docs = {
        path.stem: parse_label_file(path)
        for path in sorted(annotations_root.glob(f"*/*_{channel}.txt"))
    }
    label_batches = {
        path.stem: path.parent.name
        for path in sorted(annotations_root.glob(f"*/*_{channel}.txt"))
    }
    occurrences: list[PairOccurrence] = []
    srt_files_scanned = 0
    invalid_srt_count = 0
    for srt_path in sorted(srt_root.rglob(f"*_{channel}.srt")):
        source_stem = srt_path.stem
        label_doc = label_docs.get(source_stem)
        if label_doc is None or label_doc.exclusion_reasons:
            continue
        blocks = _parse_srt_text_blocks(srt_path)
        srt_files_scanned += 1
        if not blocks:
            invalid_srt_count += 1
            continue
        run_id, variant = _run_metadata(srt_root, srt_path)
        for srt_block in blocks:
            label_block = _matching_label_block(
                label_doc.blocks,
                srt_block.midpoint_sec,
                tolerance_sec,
            )
            if label_block is None or not label_block.normalized_text:
                continue
            occurrences.extend(
                extract_pair_occurrences(
                    hyp_text=srt_block.text,
                    ref_text=label_block.normalized_text,
                    source_stem=source_stem,
                    run_id=run_id,
                    variant=variant,
                    batch=label_batches[source_stem],
                )
            )
    return PairMiningResult(
        candidates=aggregate_pair_occurrences(occurrences),
        occurrence_count=len(occurrences),
        srt_files_scanned=srt_files_scanned,
        invalid_srt_count=invalid_srt_count,
        label_count=len(label_docs),
    )


def write_pair_candidates_csv(candidates: list[PairCandidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
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
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            row = candidate.to_dict()
            row["source_files"] = ";".join(candidate.source_files)
            row["source_runs"] = ";".join(candidate.source_runs)
            row["risk_flags"] = ";".join(candidate.risk_flags)
            writer.writerow(row)


def write_pair_candidates_jsonl(candidates: list[PairCandidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(candidate.to_dict(), ensure_ascii=False) for candidate in candidates]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def render_pair_mining_report(
    candidate_count: int,
    occurrence_count: int,
    srt_files_scanned: int = 0,
    invalid_srt_count: int = 0,
    label_count: int = 0,
) -> str:
    return "\n".join(
        [
            "# Misrecognition Pair Mining",
            "",
            "## Summary",
            "",
            f"- Labels loaded: {label_count}",
            f"- SRT files scanned: {srt_files_scanned}",
            f"- Invalid SRT files skipped: {invalid_srt_count}",
            f"- Pair occurrences: {occurrence_count}",
            f"- Candidate pairs: {candidate_count}",
            "",
            "## Notes",
            "",
            "- This report intentionally omits actual wrong/right surfaces.",
            "- Full candidate CSV/JSONL is a local ignored artifact under `outputs/pair_mining/`.",
            "- Candidates require P18 review before becoming correction rules.",
            "",
        ]
    )


def _expand_to_token_boundary(text: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    while end < len(text) and not text[end : end + 1].isspace():
        end += 1
    return start, end


def _is_valid_pair(wrong: str, right: str) -> bool:
    if not wrong or not right or wrong == right:
        return False
    if len(wrong) > 40 or len(right) > 40:
        return False
    if wrong.isdigit() or right.isdigit():
        return False
    if len(HANGUL_PATTERN.findall(wrong)) < 2 or len(HANGUL_PATTERN.findall(right)) < 2:
        return False
    return True


def _risk_flags_for(source_files: list[str], confidence: float) -> list[str]:
    flags: list[str] = []
    if len(source_files) == 1:
        flags.append("single_file_only")
    if confidence < 0.35:
        flags.append("low_alignment_confidence")
    return flags


def _parse_srt_text_blocks(path: Path) -> list[SrtTextBlock]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    blocks: list[SrtTextBlock] = []
    index = 0
    while index < len(lines):
        match = TIMESTAMP_PATTERN.fullmatch(lines[index].strip())
        if match is None:
            index += 1
            continue
        text_lines: list[str] = []
        index += 1
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1
        text = normalize_pair_surface(" ".join(text_lines))
        if text:
            blocks.append(
                SrtTextBlock(
                    start_sec=_parse_srt_timestamp(match.group("start")),
                    end_sec=_parse_srt_timestamp(match.group("end")),
                    text=text,
                )
            )
    return blocks


def _matching_label_block(
    blocks: list[LabelBlock],
    midpoint_sec: float,
    tolerance_sec: float,
) -> LabelBlock | None:
    indexed_blocks = [
        block
        for block in blocks
        if block.start_sec is not None and block.end_sec is not None
    ]
    for block in indexed_blocks:
        assert block.start_sec is not None
        assert block.end_sec is not None
        if block.start_sec - tolerance_sec <= midpoint_sec <= block.end_sec + tolerance_sec:
            return block
    if len(blocks) == 1 and blocks[0].index is None:
        return blocks[0]
    return None


def _parse_srt_timestamp(value: str) -> float:
    hours = int(value[0:2])
    minutes = int(value[3:5])
    seconds = int(value[6:8])
    millis = int(value[9:12])
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def _run_metadata(root: Path, path: Path) -> tuple[str, str]:
    relative = path.relative_to(root)
    parts = relative.parts
    if len(parts) == 1:
        return "root", ""
    return parts[0], "/".join(parts[1:-1])


__all__ = [
    "PairCandidate",
    "PairMiningResult",
    "PairOccurrence",
    "aggregate_pair_occurrences",
    "extract_pair_occurrences",
    "mine_pair_candidates",
    "normalize_pair_surface",
    "render_pair_mining_report",
    "write_pair_candidates_csv",
    "write_pair_candidates_jsonl",
]
