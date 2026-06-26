# P8 HF N-best Targetability Probe Review

Date: 2026-06-26

Branch: `wbs/P8-hf-nbest-targetability`

## Scope

Reviewed P8 implementation artifacts:

- `src/whisper_wfst/targetability.py`
- `scripts/probe_targetability.py`
- `tests/test_targetability_probe.py`
- `tests/fixtures/targetability_artifact.json`
- `tests/fixtures/targetability_manifest.json`
- `docs/reports/probes/nbest_targetability_probe.md`

## Findings

No blocking implementation defects found in the P8 scope.

Validated behavior:

- P8 does not invoke the correction engine.
- Top1 and N-best oracle CER/WER are calculated.
- Domain term oracle accuracy is calculated.
- Reference surface in N-best ratio is calculated.
- Seed wrong-surface ratio is calculated separately for top1 and N-best.
- Final eval leakage policy is present in the report.

## Residual Risks

- Current report uses synthetic fixture data, not real HF audio artifacts.
- Low targetability in real data would require P10 to be interpreted as negative evidence or trigger scope review.

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
