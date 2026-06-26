from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from whisper_wfst.hf_extractor import (
    HFExtractorConfig,
    HFHypothesisOutput,
    build_nbest_artifact_from_outputs,
)
from whisper_wfst.types import NBestArtifact


@dataclass(frozen=True)
class HFDatasetRecord:
    segment_id: str
    split: str
    audio: list[float]
    sampling_rate: int
    reference_text: str
    source_wav: str
    source_start: float
    source_end: float
    cut_start: float
    cut_end: float
    cut_duration: float
    chunk_strategy: str

    @property
    def audio_ref(self) -> str:
        return f"{self.source_wav}#{self.cut_start:.3f}-{self.cut_end:.3f}"

    def manifest_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "split": self.split,
            "ref_text": self.reference_text,
            "audio_ref": self.audio_ref,
            "source_wav": self.source_wav,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "cut_start": self.cut_start,
            "cut_end": self.cut_end,
            "cut_duration": self.cut_duration,
            "sampling_rate": self.sampling_rate,
            "chunk_strategy": self.chunk_strategy,
        }


@dataclass(frozen=True)
class RealHFExtractionResult:
    dataset_path: str
    model_id: str
    requested_split: str
    total_rows: int
    selected_rows: int
    written_artifacts: int
    skipped_counts: dict[str, int]
    output_jsonl: str
    manifest_jsonl: str
    unique_hypothesis_counts: list[int]
    blockers: list[str]


def build_hf_dataset_record(row: dict[str, Any]) -> HFDatasetRecord:
    audio = row["audio"]
    if not isinstance(audio, list):
        raise ValueError("HF dataset row audio must be a raw float list")
    sampling_rate = int(row["sampling_rate"])
    if sampling_rate != 16000:
        raise ValueError(f"expected sampling_rate=16000, got {sampling_rate}")
    return HFDatasetRecord(
        segment_id=str(row["chunk_id"]),
        split=str(row["split"]),
        audio=[float(value) for value in audio],
        sampling_rate=sampling_rate,
        reference_text=str(row["text"]),
        source_wav=str(row["source_wav"]),
        source_start=float(row["source_start"]),
        source_end=float(row["source_end"]),
        cut_start=float(row["cut_start"]),
        cut_end=float(row["cut_end"]),
        cut_duration=float(row["cut_duration"]),
        chunk_strategy=str(row["chunk_strategy"]),
    )


def filter_records_for_extraction(
    records: list[HFDatasetRecord],
    *,
    max_duration_sec: float,
    limit: int | None,
) -> tuple[list[HFDatasetRecord], dict[str, int]]:
    selected: list[HFDatasetRecord] = []
    skipped: Counter[str] = Counter()
    for record in records:
        if record.cut_duration > max_duration_sec:
            skipped["over_max_duration"] += 1
            continue
        if limit is not None and len(selected) >= limit:
            skipped["limit_excluded"] += 1
            continue
        selected.append(record)
    return selected, dict(skipped)


def build_real_hf_artifact(
    *,
    record: HFDatasetRecord,
    model_id: str,
    config: HFExtractorConfig,
    outputs: list[HFHypothesisOutput],
    created_at: str = "2026-06-26T12:00:00+09:00",
) -> NBestArtifact:
    artifact = build_nbest_artifact_from_outputs(
        segment_id=record.segment_id,
        model=model_id,
        config=config,
        outputs=outputs,
        created_at=created_at,
        audio_ref=record.audio_ref,
    )
    artifact.decode_config.update(
        {
            "dataset_split": record.split,
            "source_wav": record.source_wav,
            "source_start": record.source_start,
            "source_end": record.source_end,
            "cut_start": record.cut_start,
            "cut_end": record.cut_end,
            "cut_duration": record.cut_duration,
            "chunk_strategy": record.chunk_strategy,
        }
    )
    return artifact


def write_real_hf_manifest_jsonl(records: list[HFDatasetRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(record.manifest_dict(), ensure_ascii=False, separators=(",", ":"))
        for record in records
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def render_real_hf_extraction_report(result: RealHFExtractionResult) -> str:
    unique_counts = Counter(result.unique_hypothesis_counts)
    lines = [
        "# Real HF N-best Extraction",
        "",
        "## Summary",
        "",
        f"- Dataset path: `{result.dataset_path}`",
        f"- Model: `{result.model_id}`",
        f"- Requested split: `{result.requested_split}`",
        f"- Total rows in split: {result.total_rows}",
        f"- Selected rows: {result.selected_rows}",
        f"- Written artifacts: {result.written_artifacts}",
        f"- Output JSONL: `{result.output_jsonl}`",
        f"- Manifest JSONL: `{result.manifest_jsonl}`",
        "",
        "## Skipped Counts",
        "",
        "| Reason | Count |",
        "| --- | ---: |",
    ]
    if result.skipped_counts:
        for reason, count in sorted(result.skipped_counts.items()):
            lines.append(f"| {reason} | {count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Unique Hypothesis Count Distribution",
            "",
            "| Unique hypotheses | Segments |",
            "| ---: | ---: |",
        ]
    )
    if unique_counts:
        for unique_count, segment_count in sorted(unique_counts.items()):
            lines.append(f"| {unique_count} | {segment_count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(
        [
            "",
            "## Blockers",
            "",
        ]
    )
    if result.blockers:
        for blocker in result.blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This committed report intentionally omits reference text and hypothesis text.",
            "- Full N-best and reference manifest artifacts are local ignored outputs.",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "HFDatasetRecord",
    "RealHFExtractionResult",
    "build_hf_dataset_record",
    "build_real_hf_artifact",
    "filter_records_for_extraction",
    "render_real_hf_extraction_report",
    "write_real_hf_manifest_jsonl",
]
