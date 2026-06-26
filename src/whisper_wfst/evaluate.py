from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from whisper_wfst.targetability import edit_distance


class EvaluationValidationError(ValueError):
    pass


@dataclass(frozen=True)
class EvaluationManifestEntry:
    segment_id: str
    audio_ref: str
    source_wav: str
    source_start: float
    source_end: float
    split: str
    channel: str
    is_script_span: bool
    is_free_talk: bool
    ref_text: str
    domain_terms: list[str]
    allowed_rules: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvaluationManifestEntry:
        required = [
            "segment_id",
            "audio_ref",
            "source_wav",
            "source_start",
            "source_end",
            "split",
            "channel",
            "is_script_span",
            "is_free_talk",
            "ref_text",
            "domain_terms",
            "allowed_rules",
        ]
        for field in required:
            if field not in data:
                raise EvaluationValidationError(f"missing required field: {field}")
        return cls(
            segment_id=_str(data, "segment_id"),
            audio_ref=_str(data, "audio_ref"),
            source_wav=_str(data, "source_wav"),
            source_start=float(data["source_start"]),
            source_end=float(data["source_end"]),
            split=_str(data, "split"),
            channel=_str(data, "channel"),
            is_script_span=_bool(data, "is_script_span"),
            is_free_talk=_bool(data, "is_free_talk"),
            ref_text=_str(data, "ref_text"),
            domain_terms=list(data["domain_terms"]),
            allowed_rules=list(data["allowed_rules"]),
        )


@dataclass(frozen=True)
class PredictionRow:
    segment_id: str
    top1_text: str
    corrected_text: str
    nbest_texts: list[str]
    applied_rule_ids: list[str]
    unique_hypothesis_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PredictionRow:
        return cls(
            segment_id=_str(data, "segment_id"),
            top1_text=_str(data, "top1_text"),
            corrected_text=_str(data, "corrected_text"),
            nbest_texts=list(data["nbest_texts"]),
            applied_rule_ids=list(data["applied_rule_ids"]),
            unique_hypothesis_count=int(data["unique_hypothesis_count"]),
        )


@dataclass(frozen=True)
class EvaluationResult:
    segment_count: int
    cer: float
    wer: float
    top1_cer: float
    top1_wer: float
    corrected_cer: float
    corrected_wer: float
    domain_term_accuracy: float
    nbest_oracle_cer: float
    nbest_oracle_wer: float
    domain_term_oracle_accuracy: float
    correction_precision: float
    correction_recall: float
    overcorrection_rate: float
    free_talk_correction_rate: float
    free_talk_overcorrection_rate: float
    average_unique_hypothesis_count: float
    latency_p50_ms: str
    latency_p95_ms: str


def load_evaluation_manifest(path: Path) -> list[EvaluationManifestEntry]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise EvaluationValidationError("manifest root must be a list")
    return [EvaluationManifestEntry.from_dict(row) for row in rows]


def load_prediction_rows(path: Path) -> list[PredictionRow]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [PredictionRow.from_dict(row) for row in rows]


def evaluate_predictions(
    manifest: list[EvaluationManifestEntry],
    predictions: list[PredictionRow],
) -> EvaluationResult:
    prediction_by_id = {prediction.segment_id: prediction for prediction in predictions}
    total_corrected_cer = total_corrected_wer = 0.0
    total_top1_cer = total_top1_wer = 0.0
    total_oracle_cer = total_oracle_wer = 0.0
    domain_hits = domain_oracle_hits = 0
    correct_corrections = total_corrections = needed_corrections = 0
    overcorrections = 0
    free_talk_segments = free_talk_corrections = free_talk_overcorrections = 0
    unique_counts: list[int] = []

    for entry in manifest:
        prediction = prediction_by_id[entry.segment_id]
        total_top1_cer += _cer(prediction.top1_text, entry.ref_text)
        total_top1_wer += _wer(prediction.top1_text, entry.ref_text)
        total_corrected_cer += _cer(prediction.corrected_text, entry.ref_text)
        total_corrected_wer += _wer(prediction.corrected_text, entry.ref_text)
        total_oracle_cer += min(_cer(text, entry.ref_text) for text in prediction.nbest_texts)
        total_oracle_wer += min(_wer(text, entry.ref_text) for text in prediction.nbest_texts)
        unique_counts.append(prediction.unique_hypothesis_count)

        if _contains_all_terms(prediction.corrected_text, entry.domain_terms):
            domain_hits += 1
        if any(_contains_all_terms(text, entry.domain_terms) for text in prediction.nbest_texts):
            domain_oracle_hits += 1

        changed = prediction.corrected_text != prediction.top1_text
        needed = prediction.top1_text != entry.ref_text
        correct = changed and prediction.corrected_text == entry.ref_text
        if changed:
            total_corrections += 1
        if needed:
            needed_corrections += 1
        if correct:
            correct_corrections += 1
        if changed and prediction.corrected_text != entry.ref_text:
            overcorrections += 1

        if entry.is_free_talk:
            free_talk_segments += 1
            if changed:
                free_talk_corrections += 1
            if changed and prediction.corrected_text != entry.ref_text:
                free_talk_overcorrections += 1

    count = len(manifest)
    return EvaluationResult(
        segment_count=count,
        cer=total_corrected_cer / count,
        wer=total_corrected_wer / count,
        top1_cer=total_top1_cer / count,
        top1_wer=total_top1_wer / count,
        corrected_cer=total_corrected_cer / count,
        corrected_wer=total_corrected_wer / count,
        domain_term_accuracy=domain_hits / count,
        nbest_oracle_cer=total_oracle_cer / count,
        nbest_oracle_wer=total_oracle_wer / count,
        domain_term_oracle_accuracy=domain_oracle_hits / count,
        correction_precision=_safe_div(correct_corrections, total_corrections),
        correction_recall=_safe_div(correct_corrections, needed_corrections),
        overcorrection_rate=_safe_div(overcorrections, count),
        free_talk_correction_rate=_safe_div(free_talk_corrections, free_talk_segments),
        free_talk_overcorrection_rate=_safe_div(
            free_talk_overcorrections,
            free_talk_segments,
        ),
        average_unique_hypothesis_count=sum(unique_counts) / count,
        latency_p50_ms="not_applicable",
        latency_p95_ms="not_applicable",
    )


def render_evaluation_report(result: EvaluationResult) -> str:
    return "\n".join(
        [
            "# Evaluation Baseline Report",
            "",
            "## Comparison Sets",
            "",
            "- A: top1 baseline",
            "- B: top1 + correction",
            "- C: N-best oracle",
            "- D: N-best + correction",
            "",
            "## Metrics",
            "",
            f"- Segments: {result.segment_count}",
            f"- Top1 CER: {result.top1_cer:.4f}",
            f"- Top1 WER: {result.top1_wer:.4f}",
            f"- Corrected CER: {result.corrected_cer:.4f}",
            f"- Corrected WER: {result.corrected_wer:.4f}",
            f"- Domain term accuracy: {result.domain_term_accuracy:.4f}",
            f"- N-best oracle CER: {result.nbest_oracle_cer:.4f}",
            f"- N-best oracle WER: {result.nbest_oracle_wer:.4f}",
            f"- Domain term oracle accuracy: {result.domain_term_oracle_accuracy:.4f}",
            f"- Correction precision: {result.correction_precision:.4f}",
            f"- Correction recall: {result.correction_recall:.4f}",
            f"- Overcorrection rate: {result.overcorrection_rate:.4f}",
            f"- free-talk correction rate: {result.free_talk_correction_rate:.4f}",
            f"- free-talk overcorrection rate: {result.free_talk_overcorrection_rate:.4f}",
            f"- Average unique hypothesis count: {result.average_unique_hypothesis_count:.2f}",
            f"- Latency p50 ms: {result.latency_p50_ms}",
            f"- Latency p95 ms: {result.latency_p95_ms}",
            "",
        ]
    )


def _cer(prediction: str, reference: str) -> float:
    if not reference:
        return 0.0 if not prediction else 1.0
    return edit_distance(list(prediction), list(reference)) / len(reference)


def _wer(prediction: str, reference: str) -> float:
    reference_words = reference.split()
    if not reference_words:
        return 0.0 if not prediction.split() else 1.0
    return edit_distance(prediction.split(), reference_words) / len(reference_words)


def _contains_all_terms(text: str, terms: list[str]) -> bool:
    return all(term in text for term in terms)


def _safe_div(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _str(data: dict[str, Any], field: str) -> str:
    value = data[field]
    if not isinstance(value, str):
        raise EvaluationValidationError(f"{field} must be string")
    return value


def _bool(data: dict[str, Any], field: str) -> bool:
    value = data[field]
    if not isinstance(value, bool):
        raise EvaluationValidationError(f"{field} must be bool")
    return value


__all__ = [
    "EvaluationManifestEntry",
    "EvaluationResult",
    "EvaluationValidationError",
    "PredictionRow",
    "evaluate_predictions",
    "load_evaluation_manifest",
    "load_prediction_rows",
    "render_evaluation_report",
]
