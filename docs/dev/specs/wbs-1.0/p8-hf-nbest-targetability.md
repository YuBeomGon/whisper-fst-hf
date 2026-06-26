# P8 HF N-best Targetability Probe Spec

Date: 2026-06-26

Branch: `wbs/P8-hf-nbest-targetability`

## Goal

P8는 HF N-best artifact와 reference를 사용해 N-best에 correction 가능성이 실제로 있는지 확인한다.

이 phase는 correction engine을 사용한 top1+rules vs N-best+rules 비교를 하지 않는다. 목적은 N-best 후보
자체의 targetability를 측정하는 것이다.

## Metrics

- unique hypothesis count
- top1 CER/WER
- N-best oracle CER/WER
- domain term oracle accuracy
- reference surface가 N-best 안에 있는 비율
- seed rule wrong surface가 top1에 있는 비율
- seed rule wrong surface가 N-best 안에 있는 비율

## Leakage Policy

Final eval leakage 금지 정책을 report에 포함한다. P3.5에서 final eval 유래로 표시된 rule은 final claim에
사용하지 않는다.

## Non-goals

- automatic rule promotion
- LLM 기반 rule 생성
- rule mining
- correction engine comparison

## Acceptance Criteria

- targetability report가 unique count, N-best oracle, domain oracle, seed rule wrong surface 비율을 포함한다.
- targetability가 낮으면 P10은 negative evidence run 또는 scope review로 진행한다는 risk flag를 남긴다.
- final eval leakage 금지 정책이 report에 반영된다.
- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
