# P3 Core Contracts / DTO / Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Build validated DTOs and IO helpers for N-best artifacts, correction rules, correction traces, and backend status.

**Architecture:** Keep contracts in focused dataclasses under `src/whisper_wfst/types.py`. Put JSON/JSONL artifact IO in
`artifact_io.py` and CSV rule IO in `rule_io.py`. Keep P3 free of actual WFST composition and Whisper inference.

**Tech Stack:** Python 3.11+, standard library dataclasses/json/csv, pytest, ruff.

---

## Files

- Create: `docs/ops/schema.md`
- Create: `configs/correction.yaml`
- Create: `data/correction_rules.csv`
- Create: `src/whisper_wfst/types.py`
- Create: `src/whisper_wfst/artifact_io.py`
- Create: `src/whisper_wfst/rule_io.py`
- Create: `tests/test_artifact_io.py`
- Create: `tests/test_rule_io.py`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Artifact Contract

- [ ] Write failing tests for `Hypothesis`, `NBestArtifact`, backend status, duplicate normalized hypothesis dedupe,
  JSON read/write, JSONL read/write, and invalid `asr_cost`.
- [ ] Run `uv run --group dev pytest tests/test_artifact_io.py -q` and confirm failure because modules do not exist.
- [ ] Implement `types.py` and `artifact_io.py` minimally.
- [ ] Re-run artifact tests and confirm pass.

### Task 2: Rule Contract

- [ ] Write failing tests for rule CSV read/write, boolean parsing, invalid mode, duplicate `rule_id`, invalid cost,
  and non-empty reserved context rejection.
- [ ] Run `uv run --group dev pytest tests/test_rule_io.py -q` and confirm failure because modules do not exist.
- [ ] Implement `rule_io.py` and rule DTO validation.
- [ ] Re-run rule tests and confirm pass.

### Task 3: Config and Schema Docs

- [ ] Add `configs/correction.yaml` with backend availability/fail-fast defaults from P2.
- [ ] Add `data/correction_rules.csv` sample rule file.
- [ ] Add `docs/ops/schema.md` documenting code-level schema and validation rules.
- [ ] Update index/status/WBS/changelog.

### Task 4: Verification and Review

- [ ] Run `uv run --group dev pytest -q`.
- [ ] Run `uv run --group dev ruff check .`.
- [ ] Run external git-dir `git diff --check`.
- [ ] Add P3 review document under `docs/reviews/code/`.
- [ ] Commit and push `wbs/P3-core-contracts`.

## Review Checklist

- Invalid inputs fail loudly with `ContractValidationError`.
- `left_context` and `right_context` are rejected when non-empty.
- Duplicate N-best dedupe uses `normalized_text`, then lowest `asr_cost`, then lowest `rank`.
- P2 backend unavailable result is represented in config/DTO and not hidden.
- No Whisper inference or actual WFST composition has been added in P3.
