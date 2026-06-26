# P3 Core Contracts / DTO / Config Spec

Date: 2026-06-26

Branch: `wbs/P3-core-contracts`

## Goal

P3는 N-best artifact, correction rule, correction trace, backend availability의 current contract를
코드와 문서로 고정한다. 이후 phase는 이 contract를 기준으로 WFST composition, HF extraction,
evaluation을 구현한다.

이 phase는 실제 WFST composition이나 Whisper inference를 구현하지 않는다.

## Runtime Scope

현재 PoC runtime은 HF Transformers Whisper다. CTranslate2/faster-whisper integration은 이번 PoC
범위가 아니다.

P2 결과에 따라 현재 Python 3.12.4 uv 환경에서는 `pynini`가 unavailable이다. P3 contract는
backend availability와 fail-fast 상태를 표현해야 하며, Pynini backend 사용 가능을 암묵적으로
전제하지 않는다.

## Contracts

### Hypothesis

N-best hypothesis는 다음 필드를 가진다.

| Field | Type | Rule |
| --- | --- | --- |
| `rank` | int | 1 이상 |
| `token_ids` | list[int] | 모든 값은 int |
| `raw_text` | str | ASR 원문 |
| `normalized_text` | str | NFC 등 project normalization 후 text |
| `score_source` | str | score provenance |
| `score_is_logprob` | bool | score가 log probability 성격인지 여부 |
| `length_penalty` | float/null | HF decode 설정이 있으면 기록 |
| `raw_logprob` | float/null | 복원 가능하면 기록 |
| `decoder_score` | float | runtime raw score |
| `asr_cost` | float | WFST composition용 non-negative cost |

`asr_cost`는 0 이상이어야 한다. NaN, infinity, 음수는 invalid다.

### N-best Artifact

필수 필드:

- `segment_id`
- `model`
- `runtime`
- `decode_config`
- `hypotheses`
- `created_at`

선택 필드:

- `audio_ref`

Duplicate hypothesis 기준은 `normalized_text`다. Duplicate가 있으면 가장 낮은 `asr_cost`, 그 다음
가장 낮은 `rank`를 가진 후보를 유지한다.

### Correction Rule

CSV schema:

| Field | Type | Rule |
| --- | --- | --- |
| `rule_id` | str | non-empty, file 내 unique |
| `wrong` | str | non-empty |
| `right` | str | non-empty |
| `mode` | enum | `obligatory`, `optional`, `disabled` |
| `enabled` | bool | `true` 또는 `false` |
| `priority` | int | 0 이상 |
| `cost` | float | 0 이상 finite |
| `left_context` | str | MVP reserved. non-empty면 validation error |
| `right_context` | str | MVP reserved. non-empty면 validation error |
| `source` | str | provenance hint |

`left_context`와 `right_context`는 MVP에서 silent ignore하지 않는다. non-empty 값은 반드시 reject한다.

### Backend Status

P2 결과를 반영해 backend status는 다음 필드를 가진다.

- `backend`
- `available`
- `fail_fast`
- `fallback`
- `blocker`

`available=false`이고 `fail_fast=false`인 경우에는 `fallback`이 있어야 한다.

### Correction Trace

Correction trace는 이후 correction engine이 무엇을 했는지 설명하기 위한 DTO다.

필수 필드:

- `segment_id`
- `original_text`
- `corrected_text`
- `applied_rule_ids`
- `backend_status`

P3는 trace 생성 contract만 정의한다. 실제 correction trace 생성은 P5 이후 scope다.

## IO

P3는 다음 IO helper를 제공한다.

- N-best artifact JSON read/write
- N-best artifact JSONL read/write
- correction rule CSV read/write

IO helper는 invalid input을 조용히 통과시키지 않는다. 실패 시 `ContractValidationError`를 발생시킨다.

## Deliverables

- `docs/ops/schema.md`
- `configs/correction.yaml`
- `data/correction_rules.csv`
- `src/whisper_wfst/types.py`
- `src/whisper_wfst/artifact_io.py`
- `src/whisper_wfst/rule_io.py`
- `tests/test_artifact_io.py`
- `tests/test_rule_io.py`

## Acceptance Criteria

- invalid rule은 조용히 통과하지 않는다.
- non-empty `left_context` / `right_context`는 validation error로 reject된다.
- duplicate hypothesis dedupe 기준이 code와 schema 문서에 일치한다.
- `asr_cost` 산출/검증 규칙과 score provenance 필드가 artifact contract에 명시된다.
- sample N-best artifact와 sample rule CSV가 test fixture로 존재한다.
- backend availability/fail-fast 상태가 DTO와 config에 표현된다.
- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
