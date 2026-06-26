# P5 Synthetic N-best WFST Composition MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Compose synthetic N-best artifacts with correction rules through a deterministic phrase-rule fallback engine.

**Architecture:** Keep N-best candidate helpers in `nbest_acceptor.py`, rule matching in `correction_wfst.py`, and
candidate scoring/selection in `compose.py`. Use P3 DTOs and P4 protected spans. Do not depend on Pynini in P5.

**Tech Stack:** Python 3.11+, dataclasses, standard library, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/nbest_acceptor.py`
- Create: `src/whisper_wfst/correction_wfst.py`
- Create: `src/whisper_wfst/compose.py`
- Create: `tests/test_nbest_acceptor.py`
- Create: `tests/test_correction_wfst.py`
- Create: `tests/test_composition.py`
- Create: `tests/test_overlapping_rules.py`
- Create: `docs/reviews/code/2026-06-26-p5-synthetic-nbest-wfst-review.md`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: N-best Candidates

- [ ] Write failing tests for candidate creation and lowest ASR cost selection.
- [ ] Implement `NBestCandidate` and `build_nbest_acceptor()`.
- [ ] Re-run candidate tests.

### Task 2: Rule Matching

- [ ] Write failing tests for domain phrase correction, non-match safety, length mismatch, disabled rule skip,
  and overlapping rule order.
- [ ] Implement left-to-right deterministic phrase rule matching.
- [ ] Re-run rule matching tests.

### Task 3: Composition Selection

- [ ] Write failing tests for optional keep/correct branches, obligatory correction, fallback trace, and selected cost.
- [ ] Implement `compose_nbest_with_rules()`.
- [ ] Re-run composition tests.

### Task 4: Docs and Integration

- [ ] Update WBS/status/changelog/index.
- [ ] Add review document.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- P5 does not import Pynini.
- Protected spans can block rule application.
- Overlapping rule ordering is deterministic.
- No-match fallback is explicit in result trace.
