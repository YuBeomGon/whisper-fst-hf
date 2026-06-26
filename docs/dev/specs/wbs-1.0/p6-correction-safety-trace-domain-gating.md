# P6 Correction Safety / Trace / Domain Gating Spec

Date: 2026-06-26

Branch: `wbs/P6-correction-safety-trace-domain-gating`

## Goal

P6는 overcorrection 방지와 자유대화 보호 정책을 구현한다.

P6는 P5 composition engine을 직접 사용자에게 노출하지 않는다. Correction은 항상 다음 순서를 따른다.

```text
protect spans -> domain gate -> compose -> margin decision -> trace
```

## Domain Gate

Domain gate가 닫혀 있으면 correction을 적용하지 않는다. 이 경우 obligatory rule도 적용하지 않는다.

Gate 조건은 MVP에서 다음 값으로 판단한다.

- global `domain_gate_enabled`
- segment-level `domain_allowed`

둘 중 하나라도 false면 correction은 skipped다.

## Margin

Margin은 corrected total cost가 baseline ASR cost보다 얼마나 더 비싸도 허용할지 나타낸다.

```text
cost_increase = corrected_total_cost - baseline_asr_cost
apply if cost_increase <= margin
```

작은 margin은 애매한 correction을 차단한다.

## Trace

Trace는 다음 필드를 포함한다.

- `segment_id`
- `decision`
- `source_hypothesis_rank`
- `before_text`
- `after_text`
- `asr_cost`
- `corrected_total_cost`
- `correction_cost`
- `applied_rule_ids`
- `domain_gate_open`
- `margin`
- `blocked_reason`
- `backend_strategy`

Trace는 JSON serializable이어야 한다.

## Free-talk Safety Smoke

P6는 synthetic free-talk fixture에서 correction application rate를 계산하고 report에 남긴다. Domain gate가
닫힌 free-talk fixture에서는 unexpected correction count가 0이어야 한다.

## Non-goals

- production speaker/channel classifier
- 상담원/고객 diarization
- domain LM or phrase acceptor
- real audio evaluation

## Acceptance Criteria

- domain gate off이면 correction이 적용되지 않는다.
- domain gate off이면 obligatory rule도 적용되지 않는다.
- margin이 작은 correction을 차단한다.
- protected span 내부 correction이 적용되지 않는다.
- trace가 source hypothesis rank, before/after, costs, rule ids를 포함한다.
- free-talk fixture에서 unexpected correction이 0으로 report된다.
- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
