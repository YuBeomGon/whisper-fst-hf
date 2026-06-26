# P8 HF N-best Targetability Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Measure whether N-best artifacts contain plausible correction targets before running the correction engine.

**Architecture:** Add metric logic in `targetability.py` and a small CLI in `scripts/probe_targetability.py`. Use P3
artifact/rule IO and synthetic committed fixtures for reproducible tests.

**Tech Stack:** Python 3.11+, standard library, P3 DTO/IO, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/targetability.py`
- Create: `scripts/probe_targetability.py`
- Create: `tests/test_targetability_probe.py`
- Create: `tests/fixtures/targetability_artifact.json`
- Create: `tests/fixtures/targetability_manifest.json`
- Create: `docs/reports/probes/nbest_targetability_probe.md`
- Create: `docs/reviews/code/2026-06-26-p8-hf-nbest-targetability-review.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Metrics

- [ ] Write failing tests for CER/WER, top1 vs N-best oracle, domain oracle, and seed wrong-surface ratios.
- [ ] Implement targetability metric functions.
- [ ] Re-run tests.

### Task 2: Report and CLI

- [ ] Write failing tests for report content.
- [ ] Implement markdown report renderer and CLI.
- [ ] Generate committed report.

### Task 3: Integration

- [ ] Update docs/status/WBS/changelog/index and add review.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- P8 does not call correction engine.
- Seed wrong-surface ratios are measured against top1 and N-best separately.
- Report includes final eval leakage warning.
