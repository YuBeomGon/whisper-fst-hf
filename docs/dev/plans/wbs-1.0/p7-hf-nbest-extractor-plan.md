# P7 Hugging Face Whisper N-best Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Convert HF Whisper N-best generation outputs into validated project artifacts and report N-best diversity.

**Architecture:** Put dependency-light conversion logic in `hf_extractor.py`. Keep actual model execution outside the
core tests. Provide `scripts/extract_hf_nbest.py` with a deterministic mocked output mode.

**Tech Stack:** Python 3.11+, standard library, P3 artifact DTO/IO, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/hf_extractor.py`
- Create: `scripts/extract_hf_nbest.py`
- Create: `configs/hf.yaml`
- Create: `tests/test_hf_extractor.py`
- Create: `docs/reports/probes/hf_nbest_smoke.md`
- Create: `docs/reviews/code/2026-06-26-p7-hf-nbest-extractor-review.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Artifact Conversion

- [ ] Write failing tests for mocked HF output to `NBestArtifact`.
- [ ] Implement `HFHypothesisOutput`, `HFExtractorConfig`, and `build_nbest_artifact_from_outputs()`.
- [ ] Re-run extractor tests.

### Task 2: Diversity Report

- [ ] Write failing tests for unique count, duplicate count, and score uncertainty report.
- [ ] Implement `summarize_nbest_artifact()` and markdown report rendering.
- [ ] Re-run extractor tests.

### Task 3: CLI and Docs

- [ ] Add `configs/hf.yaml`.
- [ ] Add `scripts/extract_hf_nbest.py` mocked output mode.
- [ ] Generate `docs/reports/probes/hf_nbest_smoke.md`.
- [ ] Update docs/status/WBS/changelog/index and add review.

### Task 4: Verification and Integration

- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Tests do not require model download.
- Artifact contains score provenance fields.
- Duplicate/unique count is reported.
- Actual HF runtime uncertainty is documented.
