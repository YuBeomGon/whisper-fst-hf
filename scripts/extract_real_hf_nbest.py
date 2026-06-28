from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from whisper_wfst.artifact_io import write_nbest_jsonl
from whisper_wfst.hf_audio_extractor import (
    RealHFExtractionResult,
    build_hf_dataset_record,
    build_real_hf_artifact,
    filter_records_for_extraction,
    render_real_hf_extraction_report,
    write_real_hf_manifest_jsonl,
)
from whisper_wfst.hf_extractor import HFExtractorConfig, HFHypothesisOutput

DEFAULT_DATASET_PATH = Path("/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset")
DEFAULT_OUTPUT_JSONL = Path("outputs/hf_nbest_real/nbest.jsonl")
DEFAULT_MANIFEST_JSONL = Path("outputs/hf_nbest_real/manifest.jsonl")
DEFAULT_REPORT = Path("docs/reports/experiments/real_hf_nbest_extraction.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract real HF Whisper N-best artifacts.")
    parser.add_argument("--dataset-path", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--split", default="validation")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--max-duration-sec", type=float, default=30.0)
    parser.add_argument("--model-id", default="openai/whisper-large-v3")
    parser.add_argument("--num-beams", type=int, default=20)
    parser.add_argument("--num-return-sequences", type=int, default=20)
    parser.add_argument("--length-penalty", type=float, default=1.0)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--manifest-jsonl", type=Path, default=DEFAULT_MANIFEST_JSONL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument(
        "--torch-dtype",
        choices=["auto", "float16", "float32", "bfloat16"],
        default="auto",
    )
    args = parser.parse_args(argv)

    blockers: list[str] = []
    records = _load_records(args.dataset_path, args.split)
    selected, skipped = filter_records_for_extraction(
        records,
        max_duration_sec=args.max_duration_sec,
        limit=args.limit,
    )

    config = HFExtractorConfig(
        num_beams=args.num_beams,
        num_return_sequences=args.num_return_sequences,
        length_penalty=args.length_penalty,
    )
    artifacts = []
    if args.dry_run:
        blockers.append("dry_run_requested")
    else:
        try:
            outputs_by_record = _generate_hf_outputs(
                records=selected,
                model_id=args.model_id,
                config=config,
                local_files_only=args.local_files_only,
                device=args.device,
                torch_dtype=args.torch_dtype,
            )
            created_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
            artifacts = [
                build_real_hf_artifact(
                    record=record,
                    model_id=args.model_id,
                    config=config,
                    outputs=outputs_by_record[record.segment_id],
                    created_at=created_at,
                )
                for record in selected
            ]
        except Exception as exc:  # pragma: no cover - exercised by real runtime smoke.
            blockers.append(f"{type(exc).__name__}: {exc}")

    if artifacts:
        write_nbest_jsonl(artifacts, args.output_jsonl)
    write_real_hf_manifest_jsonl(selected, args.manifest_jsonl)
    result = RealHFExtractionResult(
        dataset_path=str(args.dataset_path),
        model_id=args.model_id,
        requested_split=args.split,
        total_rows=len(records),
        selected_rows=len(selected),
        written_artifacts=len(artifacts),
        skipped_counts=skipped,
        output_jsonl=str(args.output_jsonl),
        manifest_jsonl=str(args.manifest_jsonl),
        unique_hypothesis_counts=[
            len({hypothesis.normalized_text for hypothesis in artifact.hypotheses})
            for artifact in artifacts
        ],
        blockers=blockers,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_real_hf_extraction_report(result), encoding="utf-8")
    return 1 if blockers and not args.dry_run else 0


def _load_records(dataset_path: Path, split: str):
    try:
        from datasets import load_from_disk
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env.
        raise RuntimeError("datasets package is required for real HF extraction") from exc

    dataset_dict = load_from_disk(str(dataset_path))
    if split not in dataset_dict:
        raise ValueError(f"split {split!r} not found in {dataset_path}")
    return [build_hf_dataset_record(row) for row in dataset_dict[split]]


def _generate_hf_outputs(
    *,
    records,
    model_id: str,
    config: HFExtractorConfig,
    local_files_only: bool,
    device: str,
    torch_dtype: str,
) -> dict[str, list[HFHypothesisOutput]]:
    try:
        import torch
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env.
        raise RuntimeError("torch and transformers are required for real HF extraction") from exc

    resolved_device = _resolve_device(device, torch)
    resolved_torch_dtype = _resolve_torch_dtype(torch_dtype, resolved_device, torch)
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=local_files_only)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id,
        local_files_only=local_files_only,
        torch_dtype=resolved_torch_dtype,
    )
    model.to(resolved_device)
    model.eval()

    outputs_by_record: dict[str, list[HFHypothesisOutput]] = {}
    for record in records:
        inputs = _build_processor_inputs(processor, record)
        input_features, attention_mask = _prepare_hf_generate_inputs(
            inputs,
            resolved_device=resolved_device,
            torch_dtype=resolved_torch_dtype,
            torch_module=torch,
        )
        with torch.no_grad():
            generated = model.generate(
                input_features,
                attention_mask=attention_mask,
                num_beams=config.num_beams,
                num_return_sequences=config.num_return_sequences,
                return_dict_in_generate=True,
                output_scores=True,
                length_penalty=config.length_penalty,
                language="ko",
                task="transcribe",
            )
        sequences = generated.sequences
        texts = processor.batch_decode(sequences, skip_special_tokens=True)
        scores = getattr(generated, "sequences_scores", None)
        if scores is None:
            score_values = [0.0 for _ in texts]
        else:
            score_values = [float(value) for value in scores.detach().cpu().tolist()]
        outputs_by_record[record.segment_id] = [
            HFHypothesisOutput(
                token_ids=[int(token_id) for token_id in sequence.detach().cpu().tolist()],
                text=text,
                decoder_score=score,
            )
            for sequence, text, score in zip(sequences, texts, score_values, strict=True)
        ]
    return outputs_by_record


def _build_processor_inputs(processor, record):
    return processor(
        record.audio,
        sampling_rate=record.sampling_rate,
        return_tensors="pt",
        return_attention_mask=True,
    )


def _resolve_torch_dtype(dtype: str, resolved_device: str, torch_module):
    if dtype == "auto":
        return torch_module.float16 if resolved_device == "cuda" else torch_module.float32
    if dtype == "float16":
        return torch_module.float16
    if dtype == "float32":
        return torch_module.float32
    if dtype == "bfloat16":
        return torch_module.bfloat16
    raise ValueError(f"unsupported torch dtype: {dtype}")


def _prepare_hf_generate_inputs(
    inputs,
    *,
    resolved_device: str,
    torch_dtype,
    torch_module,
):
    input_features = inputs.input_features.to(device=resolved_device, dtype=torch_dtype)
    attention_mask = getattr(inputs, "attention_mask", None)
    if attention_mask is None:
        attention_mask = torch_module.ones(
            (input_features.shape[0], input_features.shape[-1]),
            dtype=torch_module.long,
            device=resolved_device,
        )
    else:
        attention_mask = attention_mask.to(device=resolved_device)
    return input_features, attention_mask


def _resolve_device(device: str, torch_module) -> str:
    if device == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    if device == "cuda" and not torch_module.cuda.is_available():
        raise RuntimeError("cuda requested but torch.cuda.is_available() is false")
    return device


if __name__ == "__main__":
    raise SystemExit(run())
