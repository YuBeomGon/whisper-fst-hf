from pathlib import Path

import pytest

from whisper_wfst.artifact_io import (
    read_nbest_artifact,
    read_nbest_jsonl,
    write_nbest_artifact,
    write_nbest_jsonl,
)
from whisper_wfst.types import (
    BackendStatus,
    ContractValidationError,
    CorrectionTrace,
    Hypothesis,
    NBestArtifact,
)


def test_nbest_artifact_roundtrips_json_and_dedupes_normalized_text(tmp_path: Path) -> None:
    artifact = NBestArtifact(
        segment_id="seg-001",
        model="openai/whisper-large-v3",
        runtime="hf-transformers",
        decode_config={"num_beams": 20, "num_return_sequences": 20},
        hypotheses=[
            Hypothesis(
                rank=1,
                token_ids=[101, 102],
                raw_text="손해보혐을 가입하시겠습니까",
                normalized_text="손해보혐을 가입하시겠습니까",
                score_source="hf_transition_scores",
                score_is_logprob=True,
                length_penalty=1.0,
                raw_logprob=-2.0,
                decoder_score=-2.0,
                asr_cost=2.0,
            ),
            Hypothesis(
                rank=2,
                token_ids=[101, 103],
                raw_text="손해보혐을 가입하시겠습니까",
                normalized_text="손해보혐을 가입하시겠습니까",
                score_source="hf_transition_scores",
                score_is_logprob=True,
                length_penalty=1.0,
                raw_logprob=-1.5,
                decoder_score=-1.5,
                asr_cost=1.5,
            ),
            Hypothesis(
                rank=3,
                token_ids=[201, 202],
                raw_text="손해보험을 가입하시겠습니까",
                normalized_text="손해보험을 가입하시겠습니까",
                score_source="hf_transition_scores",
                score_is_logprob=True,
                length_penalty=1.0,
                raw_logprob=-2.2,
                decoder_score=-2.2,
                asr_cost=2.2,
            ),
        ],
        created_at="2026-06-26T12:00:00+09:00",
        audio_ref="sample.wav",
    )
    path = tmp_path / "artifact.json"

    write_nbest_artifact(artifact, path)
    loaded = read_nbest_artifact(path)

    assert loaded.segment_id == "seg-001"
    assert loaded.audio_ref == "sample.wav"
    assert [hyp.rank for hyp in loaded.hypotheses] == [2, 3]
    assert [hyp.normalized_text for hyp in loaded.hypotheses] == [
        "손해보혐을 가입하시겠습니까",
        "손해보험을 가입하시겠습니까",
    ]


def test_nbest_jsonl_roundtrips_multiple_artifacts(tmp_path: Path) -> None:
    artifact = NBestArtifact(
        segment_id="seg-002",
        model="openai/whisper-large-v3",
        runtime="hf-transformers",
        decode_config={"num_beams": 20},
        hypotheses=[
            Hypothesis(
                rank=1,
                token_ids=[1],
                raw_text="보험 가입",
                normalized_text="보험 가입",
                score_source="hf_transition_scores",
                score_is_logprob=True,
                length_penalty=None,
                raw_logprob=None,
                decoder_score=-0.5,
                asr_cost=0.5,
            )
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )
    path = tmp_path / "artifacts.jsonl"

    write_nbest_jsonl([artifact, artifact], path)
    loaded = read_nbest_jsonl(path)

    assert [item.segment_id for item in loaded] == ["seg-002", "seg-002"]


def test_hypothesis_rejects_invalid_asr_cost() -> None:
    with pytest.raises(ContractValidationError, match="asr_cost"):
        Hypothesis(
            rank=1,
            token_ids=[1],
            raw_text="text",
            normalized_text="text",
            score_source="hf_transition_scores",
            score_is_logprob=True,
            length_penalty=None,
            raw_logprob=None,
            decoder_score=-1.0,
            asr_cost=-0.1,
        )


def test_backend_status_requires_fallback_when_unavailable_without_fail_fast() -> None:
    with pytest.raises(ContractValidationError, match="fallback"):
        BackendStatus(
            backend="pynini",
            available=False,
            fail_fast=False,
            fallback=None,
            blocker="ModuleNotFoundError: No module named 'pynini'",
        )


def test_correction_trace_preserves_backend_status() -> None:
    trace = CorrectionTrace(
        segment_id="seg-003",
        original_text="손해보혐",
        corrected_text="손해보험",
        applied_rule_ids=["R_SAMPLE_001"],
        backend_status=BackendStatus(
            backend="pynini",
            available=False,
            fail_fast=True,
            fallback=None,
            blocker="ModuleNotFoundError: No module named 'pynini'",
        ),
    )

    as_dict = trace.to_dict()
    loaded = CorrectionTrace.from_dict(as_dict)

    assert loaded.backend_status.backend == "pynini"
    assert loaded.backend_status.available is False
    assert loaded.backend_status.fail_fast is True


def test_committed_nbest_fixture_is_valid() -> None:
    fixture = Path("tests/fixtures/nbest_artifact.json")

    artifact = read_nbest_artifact(fixture)

    assert artifact.segment_id == "fixture-seg-001"
    assert artifact.runtime == "hf-transformers"
    assert artifact.hypotheses[0].score_source == "hf_transition_scores"
