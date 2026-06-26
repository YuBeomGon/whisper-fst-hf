# P17 Misrecognition Pair Mining Review

Date: 2026-06-26

Branch: `wbs/v2/P17-misrecognition-pair-mining`

## Scope

- Added phrase-level pair mining from normalized label blocks and matched SRT blocks.
- Added run/file/batch/variant support aggregation.
- Added local ignored candidate CSV/JSONL output and committed aggregate report only.

## Findings

- No blocking code issue found in the implemented P17 scope.
- Actual mining produced 104,924 candidate pairs from 3,081,419 occurrences, so this output is intentionally not a rule set.
- Candidate volume indicates noisy alignment and repeated sweep artifacts; P18 must enforce split provenance, support thresholds, and risk rejection before any rule seed is produced.

## Verification

- `uv run --group dev pytest tests/test_pair_mining.py -q`
- `uv run --group dev pytest -q` -> 80 passed
- `uv run --group dev ruff check .` -> passed
- `git diff --check` -> passed

## Residual Risk

- P17 uses approximate 30-second label windows, so phrase candidates can include broad local mismatch noise.
- Actual candidate surfaces are stored only under ignored `outputs/pair_mining/` artifacts and require manual or policy-driven P18 review.
