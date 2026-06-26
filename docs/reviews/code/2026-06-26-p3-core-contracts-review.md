# P3 Core Contracts / DTO / Config Review

Date: 2026-06-26

Branch: `wbs/P3-core-contracts`

## Scope

Reviewed P3 implementation artifacts:

- `src/whisper_wfst/types.py`
- `src/whisper_wfst/artifact_io.py`
- `src/whisper_wfst/rule_io.py`
- `tests/test_artifact_io.py`
- `tests/test_rule_io.py`
- `docs/ops/schema.md`
- `configs/correction.yaml`
- `data/correction_rules.csv`
- `tests/fixtures/nbest_artifact.json`
- `tests/fixtures/correction_rules.csv`

## Findings

No blocking implementation defects found in the P3 scope.

Validated behavior:

- Invalid `asr_cost` is rejected.
- Correction rule mode, cost, priority, and enabled fields are validated.
- Non-empty `left_context` is rejected instead of silently ignored.
- Duplicate `rule_id` values are rejected by CSV reader.
- Duplicate N-best hypotheses are deduped by `normalized_text`, then lowest `asr_cost`, then lowest `rank`.
- P2 backend unavailable state is represented by `BackendStatus` and `configs/correction.yaml`.

## Residual Risks

- YAML config is committed as an operational contract but is not parsed by code in P3.
- Actual WFST composition remains out of scope until P5.
- Rule provenance and leakage review are deferred to P3.5.

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
