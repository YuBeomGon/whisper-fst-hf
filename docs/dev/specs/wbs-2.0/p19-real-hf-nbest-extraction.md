# P19 Real HF N-best Extraction Spec

Date: 2026-06-26

Branch: `wbs/v2/P19-real-hf-nbest-extraction`

## Goal

Extract real HF Transformers Whisper N-best artifacts from the AIG HF chunk dataset.

P19 uses the HF dataset documented in `docs/assets/aig_domain_data_context.md`, not the P14
file-stem audio inventory.

## Dataset

```text
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset
```

Expected splits:

- `train`: 2,556 rows
- `validation`: 424 rows

Required row fields:

- `audio`: raw float waveform list
- `sampling_rate`: 16000
- `text`: reference transcript
- `chunk_id`
- `source_wav`
- `source_start`, `source_end`
- `cut_start`, `cut_end`, `cut_duration`
- `chunk_strategy`

`validation` is the default P19 smoke/evaluation split.

## Extraction Policy

- HF runtime only; CT2/faster-whisper remains out of scope.
- Default model: `openai/whisper-large-v3`.
- Default decode: `num_beams=20`, `num_return_sequences=20`, `length_penalty=1.0`.
- Local cache execution is supported with `--local-files-only`.
- Chunks longer than 30 seconds are skipped by default.
- Full N-best artifacts and reference manifest are local ignored outputs.
- Committed reports omit raw reference and hypothesis text.

## Outputs

Committed:

```text
src/whisper_wfst/hf_audio_extractor.py
scripts/extract_real_hf_nbest.py
configs/hf-real.yaml
docs/reports/experiments/real_hf_nbest_extraction.md
docs/reviews/code/2026-06-26-p19-real-hf-nbest-extraction-review.md
```

Ignored/local:

```text
outputs/hf_nbest_real/nbest.jsonl
outputs/hf_nbest_real/manifest.jsonl
```

## Acceptance Criteria

- HF dataset row schema is validated by tests.
- Manifest preserves local `ref_text` for P20 while committed reports remain redacted.
- N-best artifact output uses the existing `NBestArtifact` contract.
- Real extraction either writes at least one artifact or records a clear blocker.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
