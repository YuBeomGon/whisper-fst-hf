# P9 Evaluation Harness Review

Date: 2026-06-26

Branch: `wbs/P9-evaluation-harness`

## Scope

Reviewed P9 implementation artifacts:

- `src/whisper_wfst/evaluate.py`
- `scripts/evaluate_corrections.py`
- `tests/test_evaluate.py`
- `tests/test_evaluation_manifest.py`
- `tests/fixtures/evaluation_manifest.json`
- `tests/fixtures/evaluation_predictions.json`
- `docs/reports/probes/evaluation_baseline.md`

## Findings

No blocking implementation defects found in the P9 scope.

Validated behavior:

- Manifest validation covers source wav, source timing, channel, script/free-talk flags, ref text, domain terms, and allowed rules.
- Top1 and corrected CER/WER are separated.
- N-best oracle CER/WER and domain term oracle accuracy are reported.
- Correction precision/recall and overcorrection rate are reported.
- Free-talk correction and overcorrection rates are reported separately.
- Latency fields remain `not_applicable` when unavailable.
- A/B/C/D comparison labels are fixed in the report.

## Residual Risks

- P9 uses synthetic fixtures and does not run real audio.
- Full pipeline artifact checksums are deferred to P10.

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
