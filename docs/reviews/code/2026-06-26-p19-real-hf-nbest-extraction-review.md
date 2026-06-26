# P19 Real HF N-best Extraction Review

Date: 2026-06-26

Branch: `wbs/v2/P19-real-hf-nbest-extraction`

## Scope

- Added HF dataset row conversion and manifest generation.
- Added real HF extraction CLI with optional runtime imports.
- Added config for validation split, `openai/whisper-large-v3`, beam 20, return 20.
- Documented the current runtime blocker.

## Findings

- No blocking code issue found in the implemented adapter and artifact-writing scope.
- `uv` test environment does not include `datasets`, `transformers`, `torch`, or `numpy`.
- System Python has those packages and can read the HF dataset.
- The current machine has no CUDA device.
- `openai/whisper-large-v3` beam 20 / return 20 on CPU did not finish one 1.72s validation chunk after more than 120 seconds, so P19 real extraction is blocked on available hardware/settings.

## Verification

- `uv run --group dev pytest tests/test_real_hf_extraction.py -q` -> 4 passed
- `uv run --group dev ruff check src/whisper_wfst/hf_audio_extractor.py scripts/extract_real_hf_nbest.py tests/test_real_hf_extraction.py` -> passed
- `uv run --group dev pytest -q` -> 91 passed
- `uv run --group dev ruff check .` -> passed
- `git diff --check` -> passed

## Residual Risk

- P20 cannot proceed with real N-best evidence until P19 produces at least one real artifact.
- Running with smaller beam/model would change P19 evidence and needs explicit approval.
