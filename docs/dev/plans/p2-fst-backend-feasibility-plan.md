# P2 FST Backend Feasibility Plan

Date: 2026-06-26

## Branch

`wbs/P2-fst-backend-feasibility`

현재 작업 디렉터리의 `.git` 디렉터리가 비어 있고 쓰기 불가이므로, 이 phase는 `/tmp`의 별도
git-dir를 사용해 같은 work-tree를 추적한다. 프로젝트 파일의 `.git` 디렉터리는 수정하지 않는다.

## Implementation Steps

1. P2 spec을 작성한다.
2. failing test를 먼저 추가해 backend availability 결과와 CLI report 생성을 고정한다.
3. `src/whisper_wfst/fst_backend.py`에 Pynini availability check와 smoke runner를 구현한다.
4. `scripts/probe_fst_backend.py`에 markdown report writer를 구현한다.
5. 현재 환경에서 probe를 실행해 `docs/reports/probes/fst_backend_feasibility.md`를 생성한다.
6. review 문서에 구현 결과와 잔여 risk를 남긴다.
7. `docs/status.md`, `docs/wbs.md`, `docs/CHANGELOG.md`를 P2 결과에 맞게 갱신한다.
8. 검증 명령을 실행한다.
9. 커밋 후 remote branch로 push한다.

## Test Strategy

테스트는 Pynini 설치 여부와 무관하게 통과해야 한다. Pynini가 없으면 unavailable 결과와 report 생성이
테스트 대상이다. Pynini가 있으면 실제 smoke 결과가 포함되는 것을 확인한다.

필수 테스트:

- missing Pynini 상태를 구조화된 unavailable result로 반환한다.
- report renderer가 backend yes/no와 blocker/smoke 결과를 포함한다.
- CLI가 지정된 output path에 markdown report를 쓴다.
- Pynini가 있는 환경에서는 smoke runner가 한글 correction, compose, shortest path, roundtrip,
  space, length mismatch smoke를 실행한다.

## Verification Commands

```bash
uv run --group dev pytest -q
uv run --group dev ruff check .
uv run python scripts/probe_fst_backend.py --output docs/reports/probes/fst_backend_feasibility.md
git diff --check
```

`git diff --check`는 이번 phase의 외부 git-dir 설정을 사용해 실행한다.

## Review Checklist

- backend unavailable을 성공처럼 포장하지 않았는가?
- Pynini 미설치 환경에서도 report와 테스트가 재현 가능한가?
- P3 이후 구현이 Pynini 사용 가능을 무조건 전제하지 않도록 status/WBS에 남겼는가?
- synthetic smoke와 real N-best targetability의 경계를 명확히 유지했는가?
