from __future__ import annotations

import hashlib
import json
import re
import wave
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SPLITS = {"rule_mining", "dev_review", "eval_holdout"}


@dataclass(frozen=True)
class SourceInventoryRecord:
    source_stem: str
    channel: str
    batch: str
    label_path: str
    selected_audio_path: str | None
    audio_candidate_count: int
    split: str
    exclusion_reasons: list[str]
    label_index_count: int
    rough_text_chars: int
    audio_duration_sec: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_stem": self.source_stem,
            "channel": self.channel,
            "batch": self.batch,
            "label_path": self.label_path,
            "selected_audio_path": self.selected_audio_path,
            "audio_candidate_count": self.audio_candidate_count,
            "split": self.split,
            "exclusion_reasons": list(self.exclusion_reasons),
            "label_index_count": self.label_index_count,
            "rough_text_chars": self.rough_text_chars,
            "audio_duration_sec": self.audio_duration_sec,
        }


@dataclass(frozen=True)
class SourceInventory:
    records: list[SourceInventoryRecord]
    unmatched_audio_count: int
    duplicate_label_stem_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [record.to_dict() for record in self.records],
            "unmatched_audio_count": self.unmatched_audio_count,
            "duplicate_label_stem_count": self.duplicate_label_stem_count,
        }


def inventory_audio_text_sources(
    annotations_root: Path,
    audio_roots: list[Path],
    channel: str = "l",
) -> SourceInventory:
    label_paths = sorted(annotations_root.glob(f"*/*_{channel}.txt"))
    audio_paths = _scan_audio_paths(audio_roots, channel)
    audio_by_stem: dict[str, list[Path]] = {}
    for audio_path in audio_paths:
        audio_by_stem.setdefault(audio_path.stem, []).append(audio_path)

    label_stem_counts = Counter(path.stem for path in label_paths)
    records: list[SourceInventoryRecord] = []

    for label_path in label_paths:
        batch = label_path.parent.name
        source_stem = label_path.stem
        audio_candidates = sorted(audio_by_stem.get(source_stem, []))
        selected_audio = _select_audio_candidate(audio_candidates, batch)
        label_stats = _read_label_stats(label_path)
        exclusion_reasons: list[str] = []
        if label_stats is None:
            index_count = 0
            rough_text_chars = 0
            exclusion_reasons.append("bad_label_read")
        else:
            index_count, rough_text_chars = label_stats
            if index_count <= 2 or rough_text_chars < 120:
                exclusion_reasons.append("too_short_label")
        if selected_audio is None:
            exclusion_reasons.append("missing_audio")
        if label_stem_counts[source_stem] > 1:
            exclusion_reasons.append("duplicate_label_stem")

        records.append(
            SourceInventoryRecord(
                source_stem=source_stem,
                channel=channel,
                batch=batch,
                label_path=str(label_path),
                selected_audio_path=str(selected_audio) if selected_audio else None,
                audio_candidate_count=len(audio_candidates),
                split=assign_split(source_stem),
                exclusion_reasons=exclusion_reasons,
                label_index_count=index_count,
                rough_text_chars=rough_text_chars,
                audio_duration_sec=_read_wav_duration(selected_audio) if selected_audio else None,
            )
        )

    label_stems = {path.stem for path in label_paths}
    unmatched_audio_count = sum(1 for stem in audio_by_stem if stem not in label_stems)
    return SourceInventory(
        records=records,
        unmatched_audio_count=unmatched_audio_count,
        duplicate_label_stem_count=sum(1 for count in label_stem_counts.values() if count > 1),
    )


def assign_split(source_stem: str) -> str:
    bucket = int(hashlib.sha256(source_stem.encode("utf-8")).hexdigest(), 16) % 100
    if bucket < 60:
        return "rule_mining"
    if bucket < 80:
        return "dev_review"
    return "eval_holdout"


def write_inventory_json(inventory: SourceInventory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(inventory.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_split_manifest(inventory: SourceInventory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        record.source_stem: {
            "split": record.split,
            "channel": record.channel,
            "batch": record.batch,
            "excluded": bool(record.exclusion_reasons),
            "exclusion_reasons": list(record.exclusion_reasons),
        }
        for record in inventory.records
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_audio_text_inventory_report(inventory: SourceInventory) -> str:
    exclusion_counts = Counter(
        reason for record in inventory.records for reason in record.exclusion_reasons
    )
    split_counts = Counter(record.split for record in inventory.records)
    matched_count = sum(1 for record in inventory.records if record.selected_audio_path is not None)
    eligible_count = sum(1 for record in inventory.records if not record.exclusion_reasons)

    lines = [
        "# Audio/Text Source Inventory",
        "",
        "## Summary",
        "",
        f"- Input labels: {len(inventory.records)}",
        f"- Matched records: {matched_count}",
        f"- Eligible records: {eligible_count}",
        f"- Unmatched audio stems: {inventory.unmatched_audio_count}",
        f"- Duplicate label stems: {inventory.duplicate_label_stem_count}",
        "",
        "## Split Counts",
        "",
        "| Split | Count |",
        "| --- | ---: |",
    ]
    for split in sorted(SPLITS):
        lines.append(f"| {split} | {split_counts[split]} |")

    lines.extend(
        [
            "",
            "## Exclusion Counts",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    if exclusion_counts:
        for reason, count in sorted(exclusion_counts.items()):
            lines.append(f"| {reason} | {count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report intentionally omits raw transcript text and individual audio paths.",
            "- Full inventory JSON is a local ignored artifact under `outputs/wbs-2.0/`.",
            "",
        ]
    )
    return "\n".join(lines)


def _scan_audio_paths(audio_roots: list[Path], channel: str) -> list[Path]:
    paths: list[Path] = []
    for root in audio_roots:
        if root.exists():
            paths.extend(sorted(root.rglob(f"*_{channel}.wav")))
    return paths


def _select_audio_candidate(candidates: list[Path], batch: str) -> Path | None:
    if not candidates:
        return None

    def priority(path: Path) -> tuple[int, int, str]:
        parts = set(path.parts)
        batch_priority = 0 if batch in parts else 1
        return batch_priority, len(path.parts), str(path)

    return sorted(candidates, key=priority)[0]


def _read_label_stats(path: Path) -> tuple[int, int] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    index_count = sum(
        1 for line in text.splitlines() if re.fullmatch(r"\s*\d{1,4}\s*", line)
    )
    rough_text = re.sub(r"\[[A-Z_]{2,30}\]", " ", text)
    rough_text = re.sub(r"<[^>]{1,120}>", " ", rough_text)
    rough_text = re.sub(r"(?m)^\s*\d{1,4}\s*$", " ", rough_text)
    rough_text_chars = len(re.sub(r"\s+", "", rough_text))
    return index_count, rough_text_chars


def _read_wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wav_file:
            frame_count = wav_file.getnframes()
            frame_rate = wav_file.getframerate()
        if frame_rate <= 0:
            return None
        return round(frame_count / frame_rate, 3)
    except (OSError, EOFError, wave.Error):
        return None


__all__ = [
    "SourceInventory",
    "SourceInventoryRecord",
    "assign_split",
    "inventory_audio_text_sources",
    "render_audio_text_inventory_report",
    "write_inventory_json",
    "write_split_manifest",
]
