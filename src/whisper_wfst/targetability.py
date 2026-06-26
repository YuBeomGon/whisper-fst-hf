from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.types import CorrectionRule, NBestArtifact


@dataclass(frozen=True)
class TargetabilityResult:
    segment_count: int
    average_unique_hypotheses: float
    average_top1_cer: float
    average_nbest_oracle_cer: float
    average_top1_wer: float
    average_nbest_oracle_wer: float
    domain_term_oracle_accuracy: float
    reference_surface_in_nbest_ratio: float
    seed_wrong_surface_in_top1_ratio: float
    seed_wrong_surface_in_nbest_ratio: float
    p10_risk_flag: str


def compute_targetability(
    *,
    artifacts: list[NBestArtifact],
    references: dict[str, str],
    domain_terms: dict[str, list[str]],
    seed_rules: list[CorrectionRule],
) -> TargetabilityResult:
    if not artifacts:
        raise ValueError("artifacts must not be empty")

    top1_cer: list[float] = []
    oracle_cer: list[float] = []
    top1_wer: list[float] = []
    oracle_wer: list[float] = []
    unique_counts: list[int] = []
    domain_hits = 0
    reference_surface_hits = 0
    seed_top1_hits = 0
    seed_nbest_hits = 0

    for artifact in artifacts:
        reference = references[artifact.segment_id]
        hypotheses = sorted(artifact.hypotheses, key=lambda item: item.rank)
        top1 = hypotheses[0].normalized_text
        texts = [hypothesis.normalized_text for hypothesis in hypotheses]
        unique_counts.append(len(set(texts)))

        top1_cer.append(_cer(top1, reference))
        oracle_cer.append(min(_cer(text, reference) for text in texts))
        top1_wer.append(_wer(top1, reference))
        oracle_wer.append(min(_wer(text, reference) for text in texts))

        terms = domain_terms.get(artifact.segment_id, [])
        if terms and any(any(term in text for term in terms) for text in texts):
            domain_hits += 1
        if reference in texts:
            reference_surface_hits += 1

        wrong_surfaces = [rule.wrong for rule in seed_rules if rule.enabled]
        if any(wrong in top1 for wrong in wrong_surfaces):
            seed_top1_hits += 1
        if any(any(wrong in text for text in texts) for wrong in wrong_surfaces):
            seed_nbest_hits += 1

    segment_count = len(artifacts)
    reference_ratio = reference_surface_hits / segment_count
    risk_flag = "ok" if reference_ratio > 0 else "low_targetability_review_required"
    return TargetabilityResult(
        segment_count=segment_count,
        average_unique_hypotheses=sum(unique_counts) / segment_count,
        average_top1_cer=sum(top1_cer) / segment_count,
        average_nbest_oracle_cer=sum(oracle_cer) / segment_count,
        average_top1_wer=sum(top1_wer) / segment_count,
        average_nbest_oracle_wer=sum(oracle_wer) / segment_count,
        domain_term_oracle_accuracy=domain_hits / segment_count,
        reference_surface_in_nbest_ratio=reference_ratio,
        seed_wrong_surface_in_top1_ratio=seed_top1_hits / segment_count,
        seed_wrong_surface_in_nbest_ratio=seed_nbest_hits / segment_count,
        p10_risk_flag=risk_flag,
    )


def render_targetability_report(result: TargetabilityResult) -> str:
    return "\n".join(
        [
            "# N-best Targetability Probe",
            "",
            "## Summary",
            "",
            f"- Segments: {result.segment_count}",
            f"- Average unique hypotheses: {result.average_unique_hypotheses:.2f}",
            f"- Top1 CER: {result.average_top1_cer:.4f}",
            f"- N-best oracle CER: {result.average_nbest_oracle_cer:.4f}",
            f"- Top1 WER: {result.average_top1_wer:.4f}",
            f"- N-best oracle WER: {result.average_nbest_oracle_wer:.4f}",
            f"- Domain term oracle accuracy: {result.domain_term_oracle_accuracy:.4f}",
            f"- Reference surface in N-best ratio: {result.reference_surface_in_nbest_ratio:.4f}",
            f"- Seed wrong surface in top1 ratio: {result.seed_wrong_surface_in_top1_ratio:.4f}",
            f"- Seed wrong surface in N-best ratio: {result.seed_wrong_surface_in_nbest_ratio:.4f}",
            f"- P10 risk flag: {result.p10_risk_flag}",
            "",
            "## Policy",
            "",
            "P8 does not run the correction engine. final eval leakage candidates from "
            "P3.5 must not be used for final claims.",
            "",
        ]
    )


def edit_distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_item in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_item in enumerate(right, start=1):
            current.append(
                min(
                    previous[right_index] + 1,
                    current[right_index - 1] + 1,
                    previous[right_index - 1] + (0 if left_item == right_item else 1),
                )
            )
        previous = current
    return previous[-1]


def _cer(prediction: str, reference: str) -> float:
    if not reference:
        return 0.0 if not prediction else 1.0
    return edit_distance(list(prediction), list(reference)) / len(reference)


def _wer(prediction: str, reference: str) -> float:
    reference_words = reference.split()
    if not reference_words:
        return 0.0 if not prediction.split() else 1.0
    return edit_distance(prediction.split(), reference_words) / len(reference_words)


__all__ = [
    "TargetabilityResult",
    "compute_targetability",
    "edit_distance",
    "render_targetability_report",
]
