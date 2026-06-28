from pathlib import Path

from scripts.extract_real_hf_nbest import (
    _build_processor_inputs,
    _prepare_hf_generate_inputs,
    _resolve_torch_dtype,
)
from whisper_wfst.artifact_io import read_nbest_jsonl, write_nbest_jsonl
from whisper_wfst.hf_audio_extractor import (
    HFDatasetRecord,
    RealHFExtractionResult,
    build_hf_dataset_record,
    build_real_hf_artifact,
    filter_records_for_extraction,
    render_real_hf_extraction_report,
    write_real_hf_manifest_jsonl,
)
from whisper_wfst.hf_extractor import HFExtractorConfig, HFHypothesisOutput


def test_build_hf_dataset_record_from_hf_dataset_row() -> None:
    record = build_hf_dataset_record(
        {
            "audio": [0.0, 0.1, -0.1],
            "sampling_rate": 16000,
            "text": "보험가입금액 안내",
            "split": "validation",
            "chunk_id": "run_003_val_000001",
            "source_wav": "data/raw/wav/sample_l.wav",
            "source_start": 1.0,
            "source_end": 2.0,
            "cut_start": 1.0,
            "cut_end": 2.0,
            "cut_duration": 1.0,
            "chunk_strategy": "deterministic_non_overlap",
        }
    )

    assert record.segment_id == "run_003_val_000001"
    assert record.reference_text == "보험가입금액 안내"
    assert record.audio == [0.0, 0.1, -0.1]
    assert record.sampling_rate == 16000
    assert record.audio_ref == "data/raw/wav/sample_l.wav#1.000-2.000"


def test_filter_records_skips_over_30_second_chunks_and_applies_limit() -> None:
    records = [
        _record("short_a", 1.0),
        _record("long", 31.0),
        _record("short_b", 2.0),
    ]

    selected, skipped = filter_records_for_extraction(
        records,
        max_duration_sec=30.0,
        limit=1,
    )

    assert [record.segment_id for record in selected] == ["short_a"]
    assert skipped == {"over_max_duration": 1, "limit_excluded": 1}


def test_build_real_hf_artifact_preserves_dataset_metadata() -> None:
    config = HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0)
    artifact = build_real_hf_artifact(
        record=_record("seg-a", 1.0),
        model_id="openai/whisper-large-v3",
        config=config,
        outputs=[
            HFHypothesisOutput(token_ids=[1], text="보험가입금액", decoder_score=-1.0),
            HFHypothesisOutput(token_ids=[2], text="보험가금액", decoder_score=-1.2),
        ],
        created_at="2026-06-26T12:00:00+09:00",
    )

    assert artifact.segment_id == "seg-a"
    assert artifact.audio_ref == "sample_l.wav#0.000-1.000"
    assert artifact.decode_config["dataset_split"] == "validation"
    assert artifact.decode_config["source_wav"] == "sample_l.wav"
    assert artifact.hypotheses[0].raw_text == "보험가입금액"


def test_write_real_hf_manifest_preserves_reference_and_report_is_redacted(
    tmp_path: Path,
) -> None:
    record = _record("seg-a", 1.0)
    config = HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0)
    artifact = build_real_hf_artifact(
        record=record,
        model_id="mock",
        config=config,
        outputs=[HFHypothesisOutput(token_ids=[1], text="보험가입금액", decoder_score=-1.0)],
    )
    manifest_path = tmp_path / "manifest.jsonl"
    nbest_path = tmp_path / "nbest.jsonl"

    write_real_hf_manifest_jsonl([record], manifest_path)
    write_nbest_jsonl([artifact], nbest_path)
    loaded = read_nbest_jsonl(nbest_path)
    report = render_real_hf_extraction_report(
        RealHFExtractionResult(
            dataset_path="/dataset",
            model_id="mock",
            requested_split="validation",
            total_rows=1,
            selected_rows=1,
            written_artifacts=1,
            skipped_counts={},
            output_jsonl=str(nbest_path),
            manifest_jsonl=str(manifest_path),
            unique_hypothesis_counts=[1],
            blockers=[],
        )
    )

    assert len(loaded) == 1
    assert "seg-a" in manifest_path.read_text(encoding="utf-8")
    assert "보험가입금액" in manifest_path.read_text(encoding="utf-8")
    assert "Written artifacts: 1" in report
    assert "보험가입금액" not in report


def test_auto_torch_dtype_uses_fp16_for_cuda_and_float32_for_cpu() -> None:
    torch = _FakeTorch()

    assert _resolve_torch_dtype("auto", "cuda", torch) == torch.float16
    assert _resolve_torch_dtype("auto", "cpu", torch) == torch.float32
    assert _resolve_torch_dtype("bfloat16", "cuda", torch) == torch.bfloat16


def test_prepare_hf_generate_inputs_moves_features_and_creates_attention_mask() -> None:
    torch = _FakeTorch()
    features = _FakeTensor(shape=(1, 80, 3000))
    inputs = _FakeProcessorInputs(input_features=features)

    input_features, attention_mask = _prepare_hf_generate_inputs(
        inputs,
        resolved_device="cuda",
        torch_dtype=torch.float16,
        torch_module=torch,
    )

    assert input_features is features
    assert features.to_calls == [{"device": "cuda", "dtype": torch.float16}]
    assert attention_mask.shape == (1, 3000)
    assert torch.ones_calls == [
        {"shape": (1, 3000), "dtype": torch.long, "device": "cuda"}
    ]


def test_build_processor_inputs_requests_real_attention_mask() -> None:
    processor = _FakeProcessor()
    record = _record("seg-a", 1.0)

    inputs = _build_processor_inputs(processor, record)

    assert inputs == "processor-output"
    assert processor.calls == [
        {
            "audio": record.audio,
            "sampling_rate": 16000,
            "return_tensors": "pt",
            "return_attention_mask": True,
        }
    ]


def _record(segment_id: str, duration: float) -> HFDatasetRecord:
    return HFDatasetRecord(
        segment_id=segment_id,
        split="validation",
        audio=[0.0, 0.1],
        sampling_rate=16000,
        reference_text="보험가입금액 안내",
        source_wav="sample_l.wav",
        source_start=0.0,
        source_end=duration,
        cut_start=0.0,
        cut_end=duration,
        cut_duration=duration,
        chunk_strategy="deterministic_non_overlap",
    )


class _FakeTorch:
    float16 = "float16"
    float32 = "float32"
    bfloat16 = "bfloat16"
    long = "long"

    def __init__(self) -> None:
        self.ones_calls = []

    def ones(self, shape, *, dtype, device):  # noqa: ANN001, ANN201
        self.ones_calls.append({"shape": shape, "dtype": dtype, "device": device})
        return _FakeTensor(shape=shape)


class _FakeTensor:
    def __init__(self, *, shape) -> None:  # noqa: ANN001
        self.shape = shape
        self.to_calls = []

    def to(self, *, device, dtype=None):  # noqa: ANN001, ANN201
        call = {"device": device}
        if dtype is not None:
            call["dtype"] = dtype
        self.to_calls.append(call)
        return self


class _FakeProcessorInputs:
    def __init__(self, *, input_features) -> None:  # noqa: ANN001
        self.input_features = input_features


class _FakeProcessor:
    def __init__(self) -> None:
        self.calls = []

    def __call__(  # noqa: ANN204
        self,
        audio,
        *,
        sampling_rate,
        return_tensors,
        return_attention_mask,
    ):
        self.calls.append(
            {
                "audio": audio,
                "sampling_rate": sampling_rate,
                "return_tensors": return_tensors,
                "return_attention_mask": return_attention_mask,
            }
        )
        return "processor-output"
