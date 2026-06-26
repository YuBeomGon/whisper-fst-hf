# P10 End-to-End Offline MVP Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible synthetic offline MVP pipeline tying P7/P8/P6/P9 artifacts together.

**Architecture:** Put pipeline logic in `offline_pipeline.py`; keep CLI in `scripts/run_offline_pipeline.py`. Generated
artifacts go under ignored `outputs/offline_mvp/`, while report and manifest are committed.

**Tech Stack:** Python 3.11+, standard library JSON/hashlib/pathlib, existing project modules, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/offline_pipeline.py`
- Create: `scripts/run_offline_pipeline.py`
- Create: `tests/test_offline_pipeline.py`
- Create: `docs/reports/experiments/offline_mvp_run.md`
- Create: `docs/reports/experiments/offline_mvp_manifest.json`
- Create: `docs/reviews/code/2026-06-26-p10-offline-mvp-run-review.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Pipeline Result and Checksums

- [ ] Write failing tests that pipeline writes trace/evaluation artifacts and records sha256 checksums.
- [ ] Implement checksum and pipeline result logic.
- [ ] Re-run offline pipeline tests.

### Task 2: Report and CLI

- [ ] Write failing tests for no-production-claim report wording and targetability risk flag.
- [ ] Implement report/manifest writer and CLI.
- [ ] Generate committed report and manifest.

### Task 3: Integration

- [ ] Update docs/status/WBS/changelog/index and add review.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Generated artifacts are under ignored `outputs/`.
- Committed manifest records paths and checksums.
- Report avoids production-quality claims.
- Synthetic fixture limitation is explicit.
