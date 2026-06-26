# P11 Calibration / Rule Tuning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic calibration selection logic, report generation, and config freeze metadata.

**Architecture:** Put candidate selection in `calibration.py`; keep CLI/report generation in `scripts/run_calibration.py`.
Use synthetic candidate fixtures in tests to avoid real evaluation dependency.

**Tech Stack:** Python 3.11+, dataclasses/hashlib/json/pathlib, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/calibration.py`
- Create: `scripts/run_calibration.py`
- Create: `tests/test_calibration.py`
- Create: `docs/reports/experiments/correction_calibration.md`
- Create: `docs/reviews/code/2026-06-26-p11-calibration-rule-tuning-review.md`
- Modify: `configs/correction.yaml`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Selection Logic

- [ ] Write failing tests for hard gate filtering and deterministic best config selection.
- [ ] Implement calibration candidate and gate logic.
- [ ] Re-run calibration tests.

### Task 2: Report and Freeze

- [ ] Write failing tests for report content and checksum freeze.
- [ ] Implement report renderer and CLI.
- [ ] Generate committed calibration report.

### Task 3: Integration

- [ ] Update `configs/correction.yaml` with selected policy metadata.
- [ ] Update docs/status/WBS/changelog/index and add review.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Best config is selected only from hard-gate passing candidates.
- Free-talk risk is reported with domain metric improvement.
- Freeze checksums are present.
- Report does not claim final production quality.
