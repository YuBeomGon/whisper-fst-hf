# ADR 0001: Continue PoC With Scope Change

Date: 2026-06-26

## Status

Accepted

## Decision

Continue the PoC, but limit claims to engineering feasibility until real HF audio evaluation is complete.

## Context

P2-P12 established contracts, fallback composition, safety gates, mocked HF extraction, targetability/evaluation
reports, synthetic offline pipeline, and calibration selection. However, real audio/model inference and Pynini backend
availability remain unresolved.

## Consequences

- Continue development with real-data validation as the next priority.
- Do not claim domain ASR quality improvement from synthetic results.
- Keep teacher-force rescore out of current MVP until real N-best evidence warrants it.
