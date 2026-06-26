# P12 Optional Teacher-Force Rescore Design

Date: 2026-06-26

Branch: `wbs/P12-teacher-force-rescore-design`

## Goal

P12는 N-best + WFST fallback만으로 부족할 경우 Whisper teacher-forcing rescore를 추가할지 판단한다.

## Current Evidence

Current MVP evidence is synthetic:

- P7 validates mocked HF N-best artifact conversion, not real model/audio inference.
- P8 synthetic targetability has positive oracle signal.
- P10 synthetic offline run is reproducible, but does not prove real audio quality.
- P11 calibration is synthetic and not a held-out real audio sweep.

## Decision

Teacher-force rescore is not added to the current MVP scope.

Reason:

- Real HF model/audio score behavior is not yet measured.
- Adding teacher-force rescore now would expand runtime dependency and latency before proving N-best targetability on
  real samples.
- Current next valuable evidence is real HF N-best targetability and evaluation, not another scoring layer.

## If Added Later

Follow-up WBS should define:

- Input: corrected candidate list per segment
- Output: teacher-forced score per candidate
- Metric: improvement over P10/P11 selected config
- Hard gate: no free-talk regression
- Latency budget: per segment p50/p95
- Fallback: if teacher-force scoring fails, keep P11 config result

## Non-goals

- P10 MVP scope change
- Teacher-force implementation
- GPU performance optimization

## Acceptance Criteria

- Rescore yes/no decision is recorded.
- Rationale links to current evidence limits.
- Follow-up WBS input/output/metric outline is defined if implementation becomes necessary.
