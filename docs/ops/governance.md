# Governance

최종 갱신: 2026-06-26

## 1. 문서 등급

| Class | Path | Rule |
| --- | --- | --- |
| Current SSOT | `docs/dev/specs/project-design.md`, `docs/wbs.md` | 현재 설계와 실행 기준 |
| Status | `docs/status.md`, `docs/CHANGELOG.md` | 현재 상태와 변경 이력 |
| Operations | `docs/ops/**` | 작업 방식, 환경, 평가 정책 |
| Reports | `docs/reports/**` | 조사, 실험, audit 결과 |
| Reviews | `docs/reviews/**` | review 기록 |
| Assets | `docs/assets/**` | read-only reference |

## 2. SSOT 원칙

- WBS current 문서는 `docs/wbs.md`다.
- 전체 프로젝트 설계 current 문서는 `docs/dev/specs/project-design.md`다.
- `docs/ops/**`는 SSOT를 대체하지 않고 링크하거나 세부 운영 규칙을 둔다.
- 오래된 review나 report가 current 문서와 충돌하면 current SSOT를 우선한다.

## 3. Assets 정책

- `docs/assets/**`는 원본 또는 reference로 취급한다.
- asset 내용은 직접 수정하지 않는다.
- asset 기반 해석, 요약, 파생 설계는 `docs/reports/**` 또는 current SSOT에 반영한다.

## 4. 작업 단위

- 모든 구현은 `docs/wbs.md`의 phase ID를 기준으로 진행한다.
- phase 시작 전 관련 design/spec을 확인한다.
- phase 완료 시 `docs/status.md`와 `docs/CHANGELOG.md`를 갱신한다.
- phase 완료 주장 전 검증 명령과 결과를 확인한다.

## 5. 보호 문서

아래 문서는 변경 시 final response에 변경 이유를 명시한다.

- `AGENTS.md`
- `docs/dev/specs/project-design.md`
- `docs/wbs.md`
- `docs/ops/governance.md`
- `docs/ops/coding-conventions.md`
- `docs/ops/environment.md`
- `docs/ops/phase-loop.md`

## 6. Artifact 정책

- 큰 audio, model checkpoint, full prediction artifact는 version control 대상이 아니다.
- `outputs/`는 local run artifact 위치로 사용한다.
- commit 대상은 작은 config, schema, manifest, report, test fixture로 제한한다.
- 재현이 필요한 큰 artifact는 checksum과 생성 config를 report에 기록한다.

## 7. Commit 정책

- commit, merge, push는 사용자 명시 승인 후에만 수행한다.
- commit 전 기본 후보 검증은 `uv run --group dev ruff check .`, `uv run --group dev pytest`, `git diff --check`다.
- scaffold 전 또는 git 사용 불가 상태에서는 실행 불가 이유를 기록한다.
