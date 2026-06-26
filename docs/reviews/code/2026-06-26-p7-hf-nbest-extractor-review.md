# P7 Hugging Face Whisper N-best Extractor Review

Date: 2026-06-26

Branch: `wbs/P7-hf-nbest-extractor`

## Scope

Reviewed P7 implementation artifacts:

- `src/whisper_wfst/hf_extractor.py`
- `scripts/extract_hf_nbest.py`
- `configs/hf.yaml`
- `tests/test_hf_extractor.py`
- `docs/reports/probes/hf_nbest_smoke.md`

## Findings

No blocking implementation defects found in the P7 scope.

Validated behavior:

- Mocked HF generation output converts to P3 `NBestArtifact`.
- Decode config includes beam/return sequence settings and raw returned count.
- Hypotheses include score provenance, raw logprob, decoder score, and non-negative `asr_cost`.
- Unique and duplicate hypothesis counts are reported.
- Domain oracle and N-best oracle risk flags are explicitly unknown without reference.
- Score interpretation uncertainty is documented.

## Residual Risks

- Real HF model/audio smoke was not run in P7.
- Transformers dependency is not required by tests and remains an integration concern.
- Score calibration is deferred to later evaluation/calibration phases.

## Verification

Commands run:

```bash
uv run --group dev pytest -q
uv run --group dev ruff check .
git diff --check
```

Result:

- pytest: pass
- ruff: pass
- whitespace check: pass
