# P9 Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add validated evaluation manifest handling, metric calculation, and A/B/C/D report rendering.

**Architecture:** Keep metric and manifest code in `evaluate.py`; keep CLI report generation in
`scripts/evaluate_corrections.py`. Use synthetic JSON fixtures for tests and committed baseline report.

**Tech Stack:** Python 3.11+, dataclasses, json/pathlib, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/evaluate.py`
- Create: `scripts/evaluate_corrections.py`
- Create: `tests/test_evaluate.py`
- Create: `tests/test_evaluation_manifest.py`
- Create: `tests/fixtures/evaluation_manifest.json`
- Create: `tests/fixtures/evaluation_predictions.json`
- Create: `docs/reports/probes/evaluation_baseline.md`
- Create: `docs/reviews/code/2026-06-26-p9-evaluation-harness-review.md`
- Modify: `docs/ops/evaluation.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Manifest Validation

- [ ] Write failing tests for valid manifest and missing required fields.
- [ ] Implement `EvaluationManifestEntry` and loader.
- [ ] Re-run manifest tests.

### Task 2: Metrics

- [ ] Write failing tests for CER/WER, domain accuracy, correction precision/recall, overcorrection, and free-talk metrics.
- [ ] Implement metric calculation.
- [ ] Re-run evaluation tests.

### Task 3: Report

- [ ] Write failing tests for A/B/C/D report format and `not_applicable` unavailable metric.
- [ ] Implement report renderer and CLI.
- [ ] Generate committed baseline report.

### Task 4: Integration

- [ ] Update docs/status/WBS/changelog/index and add review.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Manifest schema includes channel/script/free-talk/source timing fields.
- Free-talk safety metrics are separate.
- Unavailable metrics do not disappear.
- P9 does not claim production quality.
