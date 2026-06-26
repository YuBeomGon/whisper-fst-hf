from __future__ import annotations

from dataclasses import dataclass

from whisper_wfst.normalize import normalized_key
from whisper_wfst.types import Hypothesis, NBestArtifact


@dataclass(frozen=True)
class HFExtractorConfig:
    num_beams: int
    num_return_sequences: int
    length_penalty: float
    return_dict_in_generate: bool = True
    output_scores: bool = True

    def to_decode_config(self) -> dict[str, int | float | bool]:
        return {
            "num_beams": self.num_beams,
            "num_return_sequences": self.num_return_sequences,
            "return_dict_in_generate": self.return_dict_in_generate,
            "output_scores": self.output_scores,
            "length_penalty": self.length_penalty,
        }


@dataclass(frozen=True)
class HFHypothesisOutput:
    token_ids: list[int]
    text: str
    decoder_score: float


@dataclass(frozen=True)
class HFNBestSummary:
    requested_hypotheses: int
    returned_hypotheses: int
    unique_hypotheses: int
    duplicate_hypotheses: int
    domain_oracle_risk_flag: str
    nbest_oracle_risk_flag: str
    score_uncertainty: str


def build_nbest_artifact_from_outputs(
    *,
    segment_id: str,
    model: str,
    config: HFExtractorConfig,
    outputs: list[HFHypothesisOutput],
    created_at: str = "2026-06-26T12:00:00+09:00",
    audio_ref: str | None = None,
) -> NBestArtifact:
    hypotheses = [
        Hypothesis(
            rank=index,
            token_ids=output.token_ids,
            raw_text=output.text,
            normalized_text=normalized_key(output.text),
            score_source="hf_transition_scores",
            score_is_logprob=True,
            length_penalty=config.length_penalty,
            raw_logprob=output.decoder_score,
            decoder_score=output.decoder_score,
            asr_cost=max(0.0, -output.decoder_score),
        )
        for index, output in enumerate(outputs, start=1)
    ]
    decode_config = config.to_decode_config()
    decode_config["raw_returned_hypotheses"] = len(outputs)
    return NBestArtifact(
        segment_id=segment_id,
        model=model,
        runtime="hf-transformers",
        decode_config=decode_config,
        hypotheses=hypotheses,
        created_at=created_at,
        audio_ref=audio_ref,
    )


def summarize_nbest_artifact(
    artifact: NBestArtifact,
    requested_hypotheses: int,
) -> HFNBestSummary:
    unique_count = len({hypothesis.normalized_text for hypothesis in artifact.hypotheses})
    returned_count = len(artifact.hypotheses)
    raw_returned_count = int(
        artifact.decode_config.get("raw_returned_hypotheses", returned_count)
    )
    return HFNBestSummary(
        requested_hypotheses=requested_hypotheses,
        returned_hypotheses=returned_count,
        unique_hypotheses=unique_count,
        duplicate_hypotheses=max(0, raw_returned_count - unique_count),
        domain_oracle_risk_flag="unknown_without_reference",
        nbest_oracle_risk_flag="unknown_without_reference",
        score_uncertainty=(
            "HF generation score interpretation is adapter-dependent; P7 records raw "
            "metadata and defers calibration."
        ),
    )


def render_hf_nbest_smoke_report(summary: HFNBestSummary) -> str:
    return "\n".join(
        [
            "# HF N-best Smoke Report",
            "",
            "## Summary",
            "",
            f"- Requested hypotheses: {summary.requested_hypotheses}",
            f"- Returned hypotheses: {summary.returned_hypotheses}",
            f"- Unique hypotheses: {summary.unique_hypotheses}",
            f"- Duplicate hypotheses: {summary.duplicate_hypotheses}",
            f"- domain oracle risk flag: {summary.domain_oracle_risk_flag}",
            f"- N-best oracle risk flag: {summary.nbest_oracle_risk_flag}",
            "",
            "## Score uncertainty",
            "",
            summary.score_uncertainty,
            "",
            "Actual model/audio smoke was not run in P7; mocked generation validates the "
            "artifact contract.",
            "",
        ]
    )


__all__ = [
    "HFExtractorConfig",
    "HFHypothesisOutput",
    "HFNBestSummary",
    "build_nbest_artifact_from_outputs",
    "render_hf_nbest_smoke_report",
    "summarize_nbest_artifact",
]
