# Phase Loop

최종 갱신: 2026-06-26

각 WBS phase는 가능한 한 아래 순서로 진행한다.

```text
WBS phase 선택
-> 관련 design/spec 확인
-> 필요한 test 먼저 작성
-> 구현
-> 검증
-> review
-> fix
-> docs/status/changelog 갱신
-> commit/merge/push는 사용자 승인 후 진행
```

## Phase Start Checklist

- `docs/status.md`를 읽고 현재 phase를 확인한다.
- active WBS 문서에서 phase 목표, 산출물, 완료 기준을 확인한다.
- WBS 1.0 이력은 `docs/wbs.md`, WBS 2.0 실행 기준은 `docs/wbs-2.0-real-hf-dataset.md`를 사용한다.
- 관련 `docs/ops/**` 또는 `docs/reports/**`를 확인한다.
- 변경할 파일과 검증 명령을 정한다.

## Phase Completion Checklist

- 완료 기준을 항목별로 확인한다.
- test/lint 또는 대체 검증을 실행한다.
- 실행하지 못한 검증은 이유를 남긴다.
- `docs/status.md`를 다음 phase 기준으로 갱신한다.
- `docs/CHANGELOG.md`에 변경 요약을 추가한다.

## Review Policy

- 설계나 WBS 변경은 가능하면 별도 review 문서 또는 final response에 근거를 남긴다.
- subagent review 결과는 `docs/reviews/**`에 보관한다.
- 실험/조사 결과는 `docs/reports/**`에 보관한다.
