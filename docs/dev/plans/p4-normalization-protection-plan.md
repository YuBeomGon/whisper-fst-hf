# P4 Normalization / Protection Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add NFC normalization and protected span placeholder handling for correction-safe text processing.

**Architecture:** Keep Unicode normalization in `normalize.py` and protected span detection/restoration in
`protect.py`. Use simple deterministic regex-based detection for structured sensitive spans and require external
spans for names.

**Tech Stack:** Python 3.11+, standard library `unicodedata`, `re`, dataclasses, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/normalize.py`
- Create: `src/whisper_wfst/protect.py`
- Create: `tests/test_unicode.py`
- Create: `tests/test_protected_spans.py`
- Create: `docs/reviews/code/2026-06-26-p4-normalization-protection-review.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Unicode Normalization

- [ ] Write failing tests that NFC and NFD Hangul produce the same normalized key.
- [ ] Implement `normalize_text()` and `normalized_key()`.
- [ ] Re-run unicode tests and confirm pass.

### Task 2: Protected Span Detection

- [ ] Write failing tests for phone, resident id, long number, money, date, URL, code, and external name spans.
- [ ] Implement `ProtectedSpan`, `ProtectedText`, and `protect_text()`.
- [ ] Re-run protected span tests and confirm pass.

### Task 3: Restore and Index Protection

- [ ] Write failing tests for restore roundtrip and protected index lookup.
- [ ] Implement `restore_text()` and `is_index_protected()`.
- [ ] Re-run protected span tests and confirm pass.

### Task 4: Docs and Review

- [ ] Update WBS/status/changelog/index.
- [ ] Add P4 review document.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Names are not auto-detected.
- Protected values restore exactly.
- Placeholder values are stable and deterministic.
- Normalization does not alter meaning beyond NFC.
