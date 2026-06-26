# P2 FST Backend Feasibility Spec

Date: 2026-06-26

Branch: `wbs/P2-fst-backend-feasibility`

## Goal

P2는 correction WFST 구현 전에 Pynini/OpenFST backend를 현재 HF PoC 환경에서 사용할 수
있는지 검증한다.

이 phase는 성능 개선 구현 phase가 아니다. 목적은 backend feasibility를 yes/no로 판단하고,
P3 이후 구현이 잘못된 전제 위에서 진행되지 않도록 하는 것이다.

## Runtime Scope

현재 PoC runtime은 HF Transformers Whisper다. CTranslate2/faster-whisper integration은
이번 PoC 범위가 아니다.

FST backend 검증은 Whisper inference 없이 synthetic text와 synthetic N-best 후보만 사용한다.

## Backend Decision Policy

P2 결과는 다음 둘 중 하나여야 한다.

| Result | Meaning | Required action |
| --- | --- | --- |
| yes | 현재 Python 환경에서 Pynini/OpenFST smoke가 통과한다 | P3 이후 Pynini backend를 구현 후보로 사용한다 |
| no | Pynini import 또는 핵심 smoke가 실패한다 | blocker와 대체 전략을 report에 남기고 P3 이후는 fail-fast 또는 fallback 전제로 진행한다 |

`no` 결과는 P2 실패가 아니라 feasibility 판단 결과다. 단, 실패 원인이 report에 남지 않거나 테스트가
backend unavailable 상태를 감추면 phase 미완료로 본다.

## Required Smoke Checks

Pynini가 import 가능한 경우 다음 smoke를 실행한다.

- Python version과 Pynini version 기록
- Unicode `utf8` token type으로 한글 acceptor 생성
- `손해보혐 -> 손해보험` correction transducer 생성
- synthetic N-best acceptor와 correction transducer compose
- shortest path 추출
- output string roundtrip
- 공백 포함 correction smoke
- 길이 차이 correction smoke

Pynini가 import 불가능한 경우 다음을 실행한다.

- import failure class와 message 기록
- backend unavailable 상태를 구조화된 결과로 반환
- CLI report 생성
- P3 이후 구현에서 사용할 fail-fast 정책 기록

## Synthetic Inputs

P2 smoke는 다음 최소 phrase를 사용한다.

| Case | Wrong | Right | Purpose |
| --- | --- | --- | --- |
| domain typo | 손해보혐 | 손해보험 | 핵심 도메인 오인식 phrase correction |
| spacing | 손해 보혐 | 손해 보험 | 공백 포함 surface 처리 |
| insertion | 보험가입 | 보험 가입 | output 길이 차이와 space insertion |

이 phase는 real ASR N-best targetability를 판단하지 않는다. 실제 N-best 안에 교정 가능한 후보가
살아 있는지는 P8에서 평가한다.

## Fail-Fast Contract

Pynini backend를 사용할 수 없는 상태에서 correction engine이 암묵적으로 동작한 것처럼 처리하면
안 된다. P2 이후 구현은 backend availability를 확인하고, unavailable이면 다음 중 하나를 택해야 한다.

- 명시적 예외로 중단한다.
- phase spec에 정의된 fallback engine으로 전환한다.
- 해당 기능을 disabled 상태로 trace에 기록한다.

## Deliverables

- `docs/reports/probes/fst_backend_feasibility.md`
- `docs/dev/plans/wbs-1.0/p2-fst-backend-feasibility-plan.md`
- `scripts/probe_fst_backend.py`
- `src/whisper_wfst/fst_backend.py`
- `tests/test_fst_backend_smoke.py`

## Acceptance Criteria

- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
- `uv run python scripts/probe_fst_backend.py --output docs/reports/probes/fst_backend_feasibility.md`
  실행 결과가 report에 남는다.
- report에는 backend yes/no, Python version, dependency 상태, smoke 결과 또는 blocker가 남는다.
- Pynini unavailable인 경우에도 결과는 구조화되고 재현 가능해야 한다.
