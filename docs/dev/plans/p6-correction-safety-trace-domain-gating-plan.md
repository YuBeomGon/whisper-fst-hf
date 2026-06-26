# P6 Correction Safety / Trace / Domain Gating Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox
> (`- [ ]`) syntax for tracking.

**Goal:** Add safety gating, margin decisions, and JSON trace output around the P5 composition engine.

**Architecture:** Put serializable trace DTOs in `trace.py`, safety policy orchestration in `safety.py`, and generate a
small free-talk smoke report from tests/fixtures-style synthetic inputs. Reuse P4 protection and P5 composition.

**Tech Stack:** Python 3.11+, dataclasses, standard library, pytest, ruff.

---

## Files

- Create: `src/whisper_wfst/trace.py`
- Create: `src/whisper_wfst/safety.py`
- Create: `tests/test_margin.py`
- Create: `tests/test_domain_gating.py`
- Create: `tests/test_trace.py`
- Create: `docs/reports/probes/free_talk_safety_smoke.md`
- Create: `docs/reviews/code/2026-06-26-p6-correction-safety-trace-domain-gating-review.md`
- Modify: `configs/correction.yaml`
- Modify: `docs/wbs.md`
- Modify: `docs/status.md`
- Modify: `docs/CHANGELOG.md`
- Modify: `docs/index.md`

## Tasks

### Task 1: Domain Gate

- [ ] Write failing tests that gate-off skips optional and obligatory corrections.
- [ ] Implement `CorrectionSafetyConfig`, `SegmentCorrectionContext`, and `apply_correction_safely()`.
- [ ] Re-run domain gate tests.

### Task 2: Margin

- [ ] Write failing tests that small margin blocks and sufficient margin applies correction.
- [ ] Implement margin decision.
- [ ] Re-run margin tests.

### Task 3: Trace

- [ ] Write failing tests for JSON trace fields.
- [ ] Implement `CorrectionDecisionTrace`.
- [ ] Re-run trace tests.

### Task 4: Free-talk Smoke

- [ ] Add free-talk safety smoke report with unexpected correction count.
- [ ] Update docs and review.
- [ ] Run full pytest, ruff, and `git diff --check`.
- [ ] Commit, push phase branch, merge to `main`, and push `main`.

## Review Checklist

- Domain gate is applied before composition.
- Obligatory rules do not bypass a closed domain gate.
- Margin blocks cost-increasing correction beyond threshold.
- Trace remains JSON serializable.
