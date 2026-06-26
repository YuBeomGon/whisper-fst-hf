# Evaluation

최종 갱신: 2026-06-26

평가 구현의 entrypoint 문서다. P9 기준 evaluation harness contract를 함께 기록한다.

현재 상세 정책:

- `docs/ops/evaluation-calibration-design.md`

현재 고정된 원칙:

- A/B/C/D 비교군을 사용한다.
- top1 + correction 비교군은 rank0-only artifact를 같은 correction engine에 통과시킨다.
- unavailable metric은 `0`이 아니라 `not_applicable`로 기록한다.
- best config는 단순 최저 CER가 아니라 hard gate 통과 후 domain metric 개선 기준으로 선택한다.
- final eval 전 config/rule/artifact checksum을 freeze한다.

P9 manifest 필수 필드:

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

P9 metric contract:

- top1 CER/WER
- corrected CER/WER
- domain term accuracy
- N-best oracle CER/WER
- domain term oracle accuracy
- correction precision/recall
- overcorrection rate
- free-talk correction rate
- free-talk overcorrection rate
- average unique hypothesis count
- latency p50/p95, unavailable이면 `not_applicable`
