# P9 Evaluation Harness Spec

Date: 2026-06-26

Branch: `wbs/P9-evaluation-harness`

## Goal

P9는 correction 효과와 risk를 offline metric으로 비교하는 evaluation harness를 구현한다.

MVP는 synthetic manifest/prediction fixture로 metric contract와 report format을 고정한다.

## Manifest Schema

필수 필드:

- `segment_id`
- `audio_ref`
- `source_wav`
- `source_start`
- `source_end`
- `split`
- `channel`
- `is_script_span`
- `is_free_talk`
- `ref_text`
- `domain_terms`
- `allowed_rules`

Invalid manifest는 조용히 통과하지 않는다.

## Metrics

- CER/WER
- domain term accuracy
- N-best oracle CER/WER
- domain term oracle accuracy
- correction precision/recall
- overcorrection rate
- free-talk correction rate
- free-talk overcorrection rate
- unique hypothesis count
- latency summary fields

Unavailable metric은 `not_applicable`로 기록한다.

## Comparison Labels

Report는 다음 비교군 이름을 고정한다.

- A: top1 baseline
- B: top1 + correction
- C: N-best oracle
- D: N-best + correction

P9는 report format을 고정한다. 실제 full offline run은 P10 scope다.

## Non-goals

- subjective transcript quality review
- production monitoring dashboard
- real audio inference

## Acceptance Criteria

- synthetic prediction/reference pair로 metric tests 통과
- evaluation input manifest validation이 통과
- unavailable metric은 `not_applicable`로 남음
- A/B/C/D comparison report format이 고정됨
- top1 + correction 비교군은 rank0 단일 hypothesis로 truncate한 artifact로 정의됨
- free-talk safety metric이 별도로 출력됨
- `uv run --group dev pytest -q`가 통과함
- `uv run --group dev ruff check .`가 통과함
