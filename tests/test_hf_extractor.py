from whisper_wfst.hf_extractor import (
    HFExtractorConfig,
    HFHypothesisOutput,
    build_nbest_artifact_from_outputs,
    render_hf_nbest_smoke_report,
    summarize_nbest_artifact,
)


def test_build_nbest_artifact_from_mocked_hf_outputs() -> None:
    artifact = build_nbest_artifact_from_outputs(
        segment_id="seg-hf",
        model="openai/whisper-large-v3",
        config=HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0),
        outputs=[
            HFHypothesisOutput(token_ids=[1, 2], text="손해보혐", decoder_score=-1.2),
            HFHypothesisOutput(token_ids=[3, 4], text="손해보험", decoder_score=-2.0),
        ],
    )

    assert artifact.runtime == "hf-transformers"
    assert artifact.decode_config["num_beams"] == 20
    assert artifact.hypotheses[0].score_source == "hf_transition_scores"
    assert artifact.hypotheses[0].score_is_logprob is True
    assert artifact.hypotheses[0].raw_logprob == -1.2
    assert artifact.hypotheses[0].asr_cost == 1.2


def test_nbest_summary_counts_unique_hypotheses_after_normalization() -> None:
    artifact = build_nbest_artifact_from_outputs(
        segment_id="seg-hf",
        model="mock",
        config=HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0),
        outputs=[
            HFHypothesisOutput(token_ids=[1], text="손해보혐", decoder_score=-1.0),
            HFHypothesisOutput(token_ids=[2], text="손해보혐", decoder_score=-1.5),
            HFHypothesisOutput(token_ids=[3], text="손해보험", decoder_score=-2.0),
        ],
    )

    summary = summarize_nbest_artifact(artifact, requested_hypotheses=20)

    assert summary.requested_hypotheses == 20
    assert summary.returned_hypotheses == 2
    assert summary.unique_hypotheses == 2
    assert summary.duplicate_hypotheses == 1
    assert summary.domain_oracle_risk_flag == "unknown_without_reference"
    assert summary.nbest_oracle_risk_flag == "unknown_without_reference"


def test_hf_nbest_smoke_report_documents_score_uncertainty() -> None:
    artifact = build_nbest_artifact_from_outputs(
        segment_id="seg-hf",
        model="mock",
        config=HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0),
        outputs=[HFHypothesisOutput(token_ids=[1], text="손해보혐", decoder_score=-1.0)],
    )

    report = render_hf_nbest_smoke_report(summarize_nbest_artifact(artifact, 20))

    assert "Unique hypotheses: 1" in report
    assert "Score uncertainty" in report
    assert "domain oracle" in report
