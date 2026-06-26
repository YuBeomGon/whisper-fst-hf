# P4 Normalization / Protection Layer Spec

Date: 2026-06-26

Branch: `wbs/P4-normalization-protection`

## Goal

P4는 correction 전에 적용할 Unicode normalization과 protected span 처리를 구현한다.

이 phase는 의미를 바꾸는 정규화, 형태소 분석, 이름 자동 탐지를 하지 않는다. 목적은 이후 P5/P6
correction engine이 동일한 normalized key와 보호된 surface를 안정적으로 사용할 수 있게 하는 것이다.

## Normalization

기본 normalization은 Unicode NFC다.

P4에서 제공하는 API:

- `normalize_text(text: str) -> str`
- `normalized_key(text: str) -> str`

`normalized_key`는 dedupe와 비교에 사용할 key다. MVP에서는 `normalize_text`와 동일하게 NFC만 적용한다.

## Protected Spans

P4는 다음 span을 보호한다.

- 전화번호
- 주민번호 형태
- 계좌번호/카드번호처럼 길게 이어진 숫자 묶음
- 증권번호처럼 영문/숫자 코드 형태
- 금액
- 날짜
- URL
- 외부 annotation으로 주입된 이름 span

이름은 자동 탐지하지 않는다. `external_spans`로 들어온 경우에만 보호한다.

Protected span API:

- `ProtectedSpan`
- `protect_text(text, external_spans=None) -> ProtectedText`
- `restore_text(text, protected_text) -> str`
- `is_index_protected(index, protected_text) -> bool`

보호는 placeholder 방식으로 처리한다. Correction engine은 placeholder 내부를 수정하지 않아야 한다.

## Span Rules

- 자동 탐지 span과 외부 span이 겹치면 merge한다.
- Placeholder는 원문 protected value를 `ProtectedText`에 보존한다.
- Restore 후 원래 protected span text가 그대로 복원되어야 한다.
- 외부 span은 `start`, `end`, `label`을 가진다. `start` inclusive, `end` exclusive다.

## Non-goals

- 형태소 분석
- 이름 자동 NER
- 의미를 바꾸는 텍스트 정규화
- correction rule 적용

## Acceptance Criteria

- NFC/NFD 한글이 같은 normalized key를 만든다.
- 전화번호, 주민번호, 긴 숫자, 금액, 날짜, URL, 코드가 보호된다.
- external name span은 보호되지만 자동 이름 탐지는 하지 않는다.
- protected placeholder restore roundtrip이 통과한다.
- protected span 내부 correction이 발생하지 않도록 index check가 가능하다.
- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
