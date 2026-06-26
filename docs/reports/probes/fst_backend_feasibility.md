# FST Backend Feasibility Report

Generated at: 2026-06-26T03:14:04.721542+00:00

## Decision

- Backend: `pynini`
- Backend available: no
- Python version: `3.12.4`
- Pynini version: `not available`
- Dependency check: import pynini from current uv/python environment
- Blocker: ModuleNotFoundError: No module named 'pynini'

## Smoke Checks

No smoke checks were executed because the backend is unavailable.

## Fail-fast policy

P3 이후 구현은 `pynini` backend availability를 먼저 확인해야 한다. backend가
unavailable이면 correction engine은 암묵적으로 성공 처리하지 말고 명시적 예외,
disabled trace, 또는 별도 fallback engine 중 하나를 선택해야 한다.

## P3 impact

P3 이후 Pynini backend를 무조건 전제하면 안 된다. dependency 설치 경로 확정 또는 fallback 전략이 필요하다.
