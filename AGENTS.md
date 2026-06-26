# Agent Guide

이 파일은 다음 세션의 작업 시작점이다.

## Read Order

1. `docs/status.md`
2. `docs/index.md`
3. `docs/wbs.md`
4. `docs/dev/specs/project-design.md`
5. 관련 `docs/ops/*.md`
6. 필요한 경우 `docs/reports/**`, `docs/reviews/**`, `docs/assets/**`

## Working Rules

- 작업은 `docs/wbs.md`의 phase ID 기준으로 진행한다.
- `docs/dev/specs/project-design.md`와 `docs/wbs.md`는 current SSOT다.
- `docs/assets/**`는 read-only reference로 취급한다.
- 큰 audio, model checkpoint, full prediction artifact는 repository에 넣지 않는다.
- 대용량 산출물은 `outputs/` 또는 외부 경로에 두고, commit 대상은 manifest, config, report, test fixture로 제한한다.
- 구현 변경은 test-first로 진행한다.
- phase 완료 시 `docs/status.md`와 `docs/CHANGELOG.md`를 갱신한다.
- commit, merge, push는 명시적 승인 후에만 수행한다.

## Current Next Step

현재 P0/P1 scaffold 이후의 다음 구현 phase는 `docs/wbs.md`의 P2 FST Backend Feasibility다.
