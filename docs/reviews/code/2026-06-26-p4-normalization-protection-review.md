# P4 Normalization / Protection Layer Review

Date: 2026-06-26

Branch: `wbs/P4-normalization-protection`

## Scope

Reviewed P4 implementation artifacts:

- `src/whisper_wfst/normalize.py`
- `src/whisper_wfst/protect.py`
- `tests/test_unicode.py`
- `tests/test_protected_spans.py`

## Findings

No blocking implementation defects found in the P4 scope.

Validated behavior:

- NFC and NFD Hangul normalize to the same key.
- Meaningful spacing is preserved.
- Structured sensitive spans are protected.
- External name spans are protected only when provided.
- Names are not auto-detected.
- Placeholder restore roundtrip preserves original protected values.
- Original-text index lookup reports protected spans.

## Residual Risks

- Regex span detection is MVP-level and intentionally conservative.
- P4 does not apply correction rules. P5/P6 must consume protected spans before correction.

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
