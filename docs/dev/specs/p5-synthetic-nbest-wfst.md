# P5 Synthetic N-best WFST Composition MVP Spec

Date: 2026-06-26

Branch: `wbs/P5-synthetic-nbest-wfst`

## Goal

P5는 음성 없이 synthetic N-best artifact와 correction rule로 weighted composition 결과를 생성한다.

P2 결과 현재 환경에서 Pynini/OpenFST backend는 unavailable이다. 따라서 P5 MVP는 Pynini를 전제하지 않고
phrase-rule 기반 deterministic fallback composition engine으로 구현한다. 이후 Pynini backend가 가능해지면
동일 contract 뒤에 backend를 교체할 수 있어야 한다.

## Inputs

- P3 `NBestArtifact`
- P3 `CorrectionRule`
- P4 protected span 정보

## Composition Model

각 hypothesis에 대해 다음 score를 계산한다.

```text
total_cost = hypothesis.asr_cost + sum(applied rule cost)
```

Candidate selection은 가장 낮은 `total_cost`, 그 다음 가장 낮은 `hypothesis.rank`를 선택한다.

## Rule Semantics

### Obligatory

`mode=obligatory`이고 `enabled=true`인 rule은 surface가 match되면 correction을 적용한다.

### Optional

`mode=optional`이고 `enabled=true`인 rule은 keep branch와 correct branch를 모두 후보로 만든다.

Optional keep branch는 명시적으로 후보로 남아야 하며, identity path가 keep cost를 무료로 우회하는 문제를
만들면 안 된다. MVP에서는 keep cost를 0으로 두고 correct branch에 rule cost를 더한다. 이후 P6 margin
policy가 optional correction 선택을 제한한다.

### Disabled

`mode=disabled` 또는 `enabled=false` rule은 적용하지 않는다.

## Deterministic Rule Order

겹치는 rule은 다음 순서로 적용 후보를 고른다.

1. wrong surface length descending
2. priority descending
3. cost ascending
4. rule_id ascending

Text scan은 left-to-right다. 같은 위치에서 여러 rule이 match되면 위 ordering으로 하나를 고른다.

## Fallback and Trace

Rule이 적용되지 않으면 lowest ASR cost hypothesis를 그대로 유지한다.

Composition result는 다음 정보를 포함한다.

- selected hypothesis rank
- original text
- corrected text
- total cost
- asr cost
- correction cost
- applied rule ids
- backend strategy
- fallback reason

## Non-goals

- HF extraction
- CT2/faster-whisper extraction
- real audio inference
- evaluation report generation
- real Pynini/OpenFST graph construction

## Acceptance Criteria

- `손해보혐 -> 손해보험` test가 통과한다.
- `혐오`가 `험오`로 바뀌지 않는다.
- 겹치는 rule deterministic order가 test로 고정된다.
- optional keep/correct branch가 test로 고정된다.
- rule 미적용 시 lowest ASR cost hypothesis가 유지된다.
- composition fallback이 trace에 남는다.
- `uv run --group dev pytest -q`가 통과한다.
- `uv run --group dev ruff check .`가 통과한다.
