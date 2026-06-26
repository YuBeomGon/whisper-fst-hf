# Coding Conventions

최종 갱신: 2026-06-26

## 1. Python

- Target Python: 3.11 이상
- Source root: `src/`
- Package: `whisper_wfst`
- Test root: `tests/`
- Public data contracts는 명시적 type annotation을 사용한다.
- 의미가 불명확한 string parsing보다 schema/DTO validation을 우선한다.

## 2. Formatting / Lint

기본 명령:

```bash
uv run --group dev ruff check .
uv run --group dev pytest
```

`ruff format` 적용 여부는 code scaffold가 안정된 뒤 별도 phase에서 확정한다.

## 3. Tests

- 새 production code는 test-first로 만든다.
- 최소 smoke test는 package import를 검증한다.
- WFST core는 synthetic fixture부터 시작한다.
- 실제 Whisper inference나 model download가 필요한 테스트는 기본 unit test에 넣지 않는다.
- 대용량 artifact가 필요한 검증은 report와 ignored `outputs/`에 기록한다.

## 4. Correction Safety

- 전역 단일 문자 substitution은 금지한다.
- protected span 내부 correction은 금지한다.
- domain gate가 off이면 obligatory rule도 적용하지 않는다.
- optional rule은 identity free bypass가 없는지 test로 고정한다.
- score sign과 cost scale은 artifact contract와 calibration report에 남긴다.

## 5. Documentation

- 설계 변경은 `docs/dev/specs/project-design.md` 또는 관련 `docs/ops/**`에 반영한다.
- 실행 순서 변경은 `docs/wbs.md`에 반영한다.
- 실험 결과는 `docs/reports/**`에 둔다.
