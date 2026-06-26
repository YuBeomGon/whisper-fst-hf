from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TIMESTAMP_PATTERN = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2},\d{3})"
)


@dataclass(frozen=True)
class SrtFileMetadata:
    path: str
    source_stem: str
    block_count: int
    first_start_sec: float | None
    last_end_sec: float | None
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source_stem": self.source_stem,
            "block_count": self.block_count,
            "first_start_sec": self.first_start_sec,
            "last_end_sec": self.last_end_sec,
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class SrtInventoryRecord:
    source_stem: str
    channel: str
    srt_path: str
    run_id: str
    variant: str
    label_matched: bool
    block_count: int
    first_start_sec: float | None
    last_end_sec: float | None
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_stem": self.source_stem,
            "channel": self.channel,
            "srt_path": self.srt_path,
            "run_id": self.run_id,
            "variant": self.variant,
            "label_matched": self.label_matched,
            "block_count": self.block_count,
            "first_start_sec": self.first_start_sec,
            "last_end_sec": self.last_end_sec,
            "is_valid": self.is_valid,
        }


@dataclass(frozen=True)
class SrtRunInventory:
    records: list[SrtInventoryRecord]

    @property
    def total_srt_count(self) -> int:
        return len(self.records)

    @property
    def matched_srt_count(self) -> int:
        return sum(1 for record in self.records if record.label_matched)

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [record.to_dict() for record in self.records],
            "total_srt_count": self.total_srt_count,
            "matched_srt_count": self.matched_srt_count,
        }


def parse_srt_file(path: Path) -> SrtFileMetadata:
    text = path.read_text(encoding="utf-8", errors="replace")
    ranges = [
        (_parse_srt_timestamp(match.group("start")), _parse_srt_timestamp(match.group("end")))
        for match in TIMESTAMP_PATTERN.finditer(text)
    ]
    if not ranges:
        return SrtFileMetadata(
            path=str(path),
            source_stem=path.stem,
            block_count=0,
            first_start_sec=None,
            last_end_sec=None,
            is_valid=False,
        )
    return SrtFileMetadata(
        path=str(path),
        source_stem=path.stem,
        block_count=len(ranges),
        first_start_sec=ranges[0][0],
        last_end_sec=ranges[-1][1],
        is_valid=True,
    )


def inventory_srt_runs(
    srt_root: Path,
    annotations_root: Path,
    channel: str = "l",
) -> SrtRunInventory:
    label_stems = {path.stem for path in annotations_root.glob(f"*/*_{channel}.txt")}
    records: list[SrtInventoryRecord] = []
    for path in sorted(srt_root.rglob(f"*_{channel}.srt")):
        metadata = parse_srt_file(path)
        run_id, variant = _run_metadata(srt_root, path)
        records.append(
            SrtInventoryRecord(
                source_stem=path.stem,
                channel=channel,
                srt_path=str(path),
                run_id=run_id,
                variant=variant,
                label_matched=path.stem in label_stems,
                block_count=metadata.block_count,
                first_start_sec=metadata.first_start_sec,
                last_end_sec=metadata.last_end_sec,
                is_valid=metadata.is_valid,
            )
        )
    return SrtRunInventory(records=records)


def write_srt_inventory_json(inventory: SrtRunInventory, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inventory.to_dict(), ensure_ascii=False, indent=2) + "\n", "utf-8")


def render_srt_run_inventory_report(inventory: SrtRunInventory) -> str:
    invalid_count = sum(1 for record in inventory.records if not record.is_valid)
    unmatched_count = sum(1 for record in inventory.records if not record.label_matched)
    run_coverage = _run_coverage(inventory.records)
    variant_counts = Counter(record.variant for record in inventory.records)

    lines = [
        "# SRT Run Inventory",
        "",
        "## Summary",
        "",
        f"- Input SRT files: {inventory.total_srt_count}",
        f"- Label matched SRT files: {inventory.matched_srt_count}",
        f"- Unmatched SRT files: {unmatched_count}",
        f"- Invalid SRT files: {invalid_count}",
        f"- Unique runs: {len({record.run_id for record in inventory.records})}",
        "",
        "## Top Run Coverage",
        "",
        "| Run | Variant | SRT files | Label matched | Valid |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for (run_id, variant), counts in sorted(
        run_coverage.items(),
        key=lambda item: (-item[1]["matched"], -item[1]["total"], item[0][0], item[0][1]),
    )[:25]:
        lines.append(
            f"| {run_id} | {variant} | {counts['total']} | "
            f"{counts['matched']} | {counts['valid']} |"
        )

    lines.extend(
        [
            "",
            "## Variant Counts",
            "",
            "| Variant | Count |",
            "| --- | ---: |",
        ]
    )
    for variant, count in sorted(variant_counts.items()):
        lines.append(f"| {variant} | {count} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report intentionally omits raw SRT transcript text and individual file paths.",
            "- Full SRT inventory JSON is a local ignored artifact under `outputs/wbs-2.0/`.",
            "",
        ]
    )
    return "\n".join(lines)


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
    run_id = parts[0]
    variant = "/".join(parts[1:-1])
    return run_id, variant


def _run_coverage(
    records: list[SrtInventoryRecord],
) -> dict[tuple[str, str], dict[str, int]]:
    coverage: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"total": 0, "matched": 0, "valid": 0}
    )
    for record in records:
        key = (record.run_id, record.variant)
        coverage[key]["total"] += 1
        coverage[key]["matched"] += int(record.label_matched)
        coverage[key]["valid"] += int(record.is_valid)
    return dict(coverage)


__all__ = [
    "SrtFileMetadata",
    "SrtInventoryRecord",
    "SrtRunInventory",
    "inventory_srt_runs",
    "parse_srt_file",
    "render_srt_run_inventory_report",
    "write_srt_inventory_json",
]
