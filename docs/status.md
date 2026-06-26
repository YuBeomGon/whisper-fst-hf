# Project Status

최종 갱신: 2026-06-26

## Current State

P0 Governance / Docs Scaffold, P1 Python Scaffold / Environment, P2 FST Backend Feasibility,
P3 Core Contracts / DTO / Config, P3.5 Rule Source Audit / Seed Rule Review,
P4 Normalization / Protection Layer, P5 Synthetic N-best WFST Composition MVP,
P6 Correction Safety / Trace / Domain Gating, P7 Hugging Face Whisper N-best Extractor,
P8 HF N-best Targetability Probe, P9 Evaluation Harness를 완료했다.

현재 기준 문서:

- `docs/dev/specs/project-design.md`
- `docs/wbs.md`
- `docs/ops/schema.md`
- `docs/ops/evaluation-calibration-design.md`

현재 PoC runtime은 HF Transformers Whisper다. CTranslate2/faster-whisper는 이번 PoC 범위가 아니다.

## Phase Status

| Phase | Status | Note |
| --- | --- | --- |
| P0 Governance / Docs Scaffold | done | 운영 문서, index, status, changelog 생성 |
| P1 Python Scaffold / Environment | done | Python package scaffold와 import smoke test 생성 |
| P2 FST Backend Feasibility | done | 현재 uv/Python 3.12.4 환경에서 `pynini` unavailable |
| P3 Core Contracts / DTO / Config | done | DTO, schema, config, JSON/JSONL/CSV IO helper 생성 |
| P3.5 Rule Source Audit / Seed Rule Review | done | safe seed 1개, review optional 1개, disabled 3개로 분리 |
| P4 Normalization / Protection Layer | done | NFC normalization과 protected span restore 구현 |
| P5 Synthetic N-best WFST Composition MVP | done | Pynini unavailable 기준 phrase-rule fallback composition 구현 |
| P6 Correction Safety / Trace / Domain Gating | done | domain gate, margin, trace, free-talk safety smoke 구현 |
| P7 Hugging Face Whisper N-best Extractor | done | mocked HF generation에서 N-best artifact/report 생성 |
| P8 HF N-best Targetability Probe | done | N-best oracle/seed surface targetability report 생성 |
| P9 Evaluation Harness | done | manifest validation, metrics, A/B/C/D report 구현 |

## Next Actions

1. P10 End-to-End Offline MVP Run을 시작한다.
2. committed fixture 기반 offline pipeline을 재현하고 report/manifest를 남긴다.
3. 실제 audio/model artifact가 없으면 synthetic offline MVP로 residual risk를 명시한다.
