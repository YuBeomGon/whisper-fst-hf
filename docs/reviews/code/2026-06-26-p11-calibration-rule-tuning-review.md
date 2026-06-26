# P11 Calibration / Rule Tuning Review

Date: 2026-06-26

Branch: `wbs/P11-calibration-rule-tuning`

## Scope

Reviewed P11 implementation artifacts:

- `src/whisper_wfst/calibration.py`
- `scripts/run_calibration.py`
- `tests/test_calibration.py`
- `docs/reports/experiments/correction_calibration.md`
- `configs/correction.yaml`

## Findings

No blocking implementation defects found in the P11 scope.

Validated behavior:

- Hard gate filters candidates with free-talk overcorrection, overcorrection, or insufficient domain accuracy.
- Best config selection is deterministic.
- Report records selected lambda, margin, beam settings, rule policy, domain gate policy, and free-talk risk.
- Freeze checksums are recorded.
- Config metadata records the selected synthetic calibration candidate.

## Residual Risks

- Calibration uses synthetic candidates, not a real held-out audio sweep.
- Final eval freeze must be repeated with real artifacts before external quality claims.

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
