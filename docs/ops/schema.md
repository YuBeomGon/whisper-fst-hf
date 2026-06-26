# Current Schema

최종 갱신: 2026-06-26

이 문서는 P3 기준 current contract다. 이후 phase는 이 schema와 `src/whisper_wfst/types.py`의
validation을 기준으로 구현한다.

## Runtime

현재 PoC runtime은 HF Transformers Whisper다. CTranslate2/faster-whisper integration은 이번 PoC
범위가 아니다.

P2 결과 현재 uv/Python 3.12.4 환경에서 `pynini`는 import되지 않는다. 따라서 P3 이후 구현은
backend availability를 명시적으로 확인해야 한다.

## N-best Artifact

Artifact root:

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `segment_id` | string | yes | non-empty |
| `model` | string | yes | non-empty |
| `runtime` | string | yes | `hf-transformers` 등 runtime id |
| `decode_config` | object | yes | HF decode config metadata |
| `hypotheses` | array | yes | `Hypothesis` list |
| `created_at` | string | yes | artifact 생성 시각 |
| `audio_ref` | string/null | no | source audio reference |

Duplicate hypothesis 기준은 `normalized_text`다. Duplicate가 있으면 가장 낮은 `asr_cost`, 그 다음
가장 낮은 `rank`를 가진 후보를 유지한다.

## Hypothesis

| Field | Type | Required | Rule |
| --- | --- | --- | --- |
| `rank` | integer | yes | 1 이상 |
| `token_ids` | array[integer] | yes | tokenizer ids |
| `raw_text` | string | yes | ASR 원문 |
| `normalized_text` | string | yes | normalization 후 text |
| `score_source` | string | yes | score provenance |
| `score_is_logprob` | boolean | yes | log probability 성격 여부 |
| `length_penalty` | number/null | yes | decode length penalty |
| `raw_logprob` | number/null | yes | 복원 가능할 때 sequence log probability |
| `decoder_score` | number | yes | runtime raw score |
| `asr_cost` | number | yes | 0 이상 finite |

`asr_cost`는 WFST composition에서 사용할 non-negative cost다. score sign이 불명확한 runtime은
ranking sanity test를 통과하기 전까지 production comparison에 사용하지 않는다.

## Correction Rule CSV

Field order is fixed:

```text
rule_id,wrong,right,mode,enabled,priority,cost,left_context,right_context,source
```

| Field | Type | Rule |
| --- | --- | --- |
| `rule_id` | string | non-empty, file 내 unique |
| `wrong` | string | non-empty |
| `right` | string | non-empty |
| `mode` | enum | `obligatory`, `optional`, `disabled` |
| `enabled` | boolean | CSV value는 `true` 또는 `false` |
| `priority` | integer | 0 이상 |
| `cost` | number | 0 이상 finite |
| `left_context` | string | MVP reserved. non-empty면 reject |
| `right_context` | string | MVP reserved. non-empty면 reject |
| `source` | string | provenance hint |

`left_context`와 `right_context`는 silent ignore하지 않는다. MVP에서는 non-empty 값을 validation error로
처리한다.

## Backend Status

| Field | Type | Rule |
| --- | --- | --- |
| `backend` | string | non-empty |
| `available` | boolean | backend 사용 가능 여부 |
| `fail_fast` | boolean | unavailable일 때 즉시 실패 여부 |
| `fallback` | string/null | `available=false` and `fail_fast=false`이면 필수 |
| `blocker` | string/null | unavailable 이유 |

P2 결과 기준 기본값은 `configs/correction.yaml`에 기록한다.

## Correction Trace

| Field | Type | Rule |
| --- | --- | --- |
| `segment_id` | string | non-empty |
| `original_text` | string | correction 전 text |
| `corrected_text` | string | correction 후 text |
| `applied_rule_ids` | array[string] | 적용 rule id 목록 |
| `backend_status` | object | Backend Status |

P3는 trace contract만 고정한다. 실제 trace 생성은 P5 이후 구현한다.
