# Project Status

최종 갱신: 2026-06-26

## Current State

P0 Governance / Docs Scaffold, P1 Python Scaffold / Environment, P2 FST Backend Feasibility,
P3 Core Contracts / DTO / Config, P3.5 Rule Source Audit / Seed Rule Review,
P4 Normalization / Protection Layer, P5 Synthetic N-best WFST Composition MVP,
P6 Correction Safety / Trace / Domain Gating, P7 Hugging Face Whisper N-best Extractor,
P8 HF N-best Targetability Probe를 완료했다.

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

## Next Actions

1. P9 Evaluation Harness를 시작한다.
2. CER/WER, domain accuracy, correction precision/recall, free-talk safety metric을 구현한다.
3. A/B/C/D comparison report format을 고정한다.
