# P5 Synthetic N-best WFST Composition MVP Review

Date: 2026-06-26

Branch: `wbs/P5-synthetic-nbest-wfst`

## Scope

Reviewed P5 implementation artifacts:

- `src/whisper_wfst/nbest_acceptor.py`
- `src/whisper_wfst/correction_wfst.py`
- `src/whisper_wfst/compose.py`
- `tests/test_nbest_acceptor.py`
- `tests/test_correction_wfst.py`
- `tests/test_composition.py`
- `tests/test_overlapping_rules.py`

## Findings

No blocking implementation defects found in the P5 scope.

Validated behavior:

- P5 does not import Pynini.
- `손해보혐 -> 손해보험` correction is covered through rule matching and obligatory composition.
- Unmatched surface such as `혐오` is not rewritten.
- Length mismatch correction works.
- Disabled rules are skipped.
- Protected spans block rule application.
- Overlapping rules use deterministic ordering.
- Optional keep branch can win when correction cost is high.
- No-rule fallback records `no_rule_applied`.

## Residual Risks

- This is a phrase-rule fallback, not a true OpenFST graph backend.
- Optional correction choice is intentionally conservative until P6 margin/domain gate policy.
- Pynini backend remains unavailable in the current environment.

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
