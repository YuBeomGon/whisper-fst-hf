# Evaluation

최종 갱신: 2026-06-26

평가 구현의 entrypoint 문서다.

현재 상세 정책:

- `docs/ops/evaluation-calibration-design.md`

P9에서 이 문서는 실제 evaluation harness 기준으로 확장한다.

현재 고정된 원칙:

- A/B/C/D 비교군을 사용한다.
- top1 + correction 비교군은 rank0-only artifact를 같은 correction engine에 통과시킨다.
- unavailable metric은 `0`이 아니라 `not_applicable`로 기록한다.
- best config는 단순 최저 CER가 아니라 hard gate 통과 후 domain metric 개선 기준으로 선택한다.
- final eval 전 config/rule/artifact checksum을 freeze한다.
