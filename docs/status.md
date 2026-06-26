# Project Status

최종 갱신: 2026-06-26

## Current State

P0 Governance / Docs Scaffold, P1 Python Scaffold / Environment, P2 FST Backend Feasibility를 완료했다.

현재 기준 문서:

- `docs/dev/specs/project-design.md`
- `docs/wbs.md`
- `docs/ops/evaluation-calibration-design.md`

현재 PoC runtime은 HF Transformers Whisper다. CTranslate2/faster-whisper는 이번 PoC 범위가 아니다.

## Phase Status

| Phase | Status | Note |
| --- | --- | --- |
| P0 Governance / Docs Scaffold | done | 운영 문서, index, status, changelog 생성 |
| P1 Python Scaffold / Environment | done | Python package scaffold와 import smoke test 생성 |
| P2 FST Backend Feasibility | done | 현재 uv/Python 3.12.4 환경에서 `pynini` unavailable |

## Next Actions

1. P3 Core Contracts / DTO / Config를 시작한다.
2. P3 contract에 backend availability/fail-fast 상태를 포함한다.
3. P5 composition 구현 전 Pynini 설치 경로 확정 또는 fallback 전략을 다시 결정한다.
