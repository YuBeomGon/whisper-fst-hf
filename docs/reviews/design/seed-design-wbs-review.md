# Seed Design / WBS Review

날짜: 2026-06-26

문서 등급: historical review record

검토 방식: subagent review

검토 대상:

- `docs/dev/specs/project-design.md`
- `docs/wbs.md`

참고 원본:

- `docs/assets/whisper_wfst_composition_research.md`

전제:

- `docs/assets/**`는 수정 불가 reference 원본이다.
- `docs/dev/specs/project-design.md`와 `docs/wbs.md`는 프로젝트 실행을 시작하기 위한 seed 문서다.
- 이 리뷰는 문체 리뷰가 아니라 실행 가능성 리뷰다.

## Blocker

### 1. WBS SSOT 경로가 충돌한다

파일/섹션:

- `docs/wbs.md` P0
- `docs/dev/specs/project-design.md` expected project structure

문제:

현재 WBS는 `docs/wbs.md`인데 P0 산출물에 `docs/ops/wbs.md`가 들어 있다. design 문서는 `docs/wbs.md`를 기준 구조로 둔다.

왜 중요한지:

다음 에이전트가 WBS SSOT를 복제하거나 이동해 current WBS가 둘로 갈라질 수 있다. P0가 바로 문서 거버넌스를 만드는 phase라 시작 전 모호하면 위험하다.

추천 수정 방향:

current WBS 경로를 `docs/wbs.md`로 고정하고, `docs/ops/wbs.md`는 제거하거나 `wbs-process.md` 같은 운영 가이드로 명확히 rename한다.

## Important

### 1. `left_context` / `right_context` 구현 범위가 불명확하다

파일/섹션:

- `docs/dev/specs/project-design.md` rule schema
- `docs/wbs.md` P3 / P5

문제:

`left_context` / `right_context` 필드는 정의돼 있지만 WBS에는 구현/검증 phase가 없다.

왜 중요한지:

context 필드가 CSV에 들어가도 엔진이 무시하면 전역 substring 교정으로 과교정이 발생할 수 있다.

추천 수정 방향:

MVP에서는 non-empty context를 reject/reserved 처리하거나, P5에 boundary/context 구현과 조사 포함 테스트를 추가한다.

### 2. optional rule의 identity bypass 금지 invariant가 WBS 완료 기준에 빠져 있다

파일/섹션:

- `docs/dev/specs/project-design.md` optional bypass
- `docs/wbs.md` P5 완료 기준

문제:

design은 optional rule에서 identity free bypass 금지를 핵심 invariant로 두지만, WBS P5 완료 기준에는 빠져 있다.

왜 중요한지:

identity가 keep_cost를 무료 우회하면 optional/keep cost 설계가 무력화된다.

추천 수정 방향:

P5 완료 기준에 "optional rule에서 identity bypass 불가" 테스트를 명시한다.

### 3. obligatory rule, domain gate, margin의 우선순위가 불명확하다

파일/섹션:

- `docs/dev/specs/project-design.md` safety
- `docs/dev/specs/project-design.md` margin
- `docs/wbs.md` P6

문제:

"obligatory는 항상 교정"인지, "domain gate off면 obligatory도 차단"인지, "margin이 obligatory에도 적용"되는지 구현이 갈릴 수 있다.

왜 중요한지:

같은 rule set으로도 구현자마다 correction 결과가 달라질 수 있다.

추천 수정 방향:

safety 적용 순서를 명시한다.

예:

```text
protect -> domain gate -> compose -> margin decision -> trace
```

### 4. 이름 보호 범위가 모호하다

파일/섹션:

- `docs/dev/specs/project-design.md` protected spans
- `docs/wbs.md` P4

문제:

design은 `이름` 보호를 포함하지만 WBS는 이름 NER를 비범위로 둔다.

왜 중요한지:

에이전트가 이름 보호를 구현해야 하는지, 외부 span만 받으면 되는지 혼동한다.

추천 수정 방향:

regex로 탐지 가능한 span과 외부 annotation으로 주입되는 span을 분리한다. 이름은 MVP에서 "external span only"인지 결정한다.

### 5. ASR cost contract가 충분히 고정되지 않았다

파일/섹션:

- `docs/dev/specs/project-design.md` ASR cost
- `docs/wbs.md` HF / CT2 phases

문제:

score sign, length penalty, normalized/raw score 선택이 contract 수준에서 충분히 고정되지 않았다.

왜 중요한지:

shortest path는 cost scale에 매우 민감하다. HF/CT2 score를 잘못 뒤집거나 섞으면 결과가 조용히 틀어진다.

추천 수정 방향:

P3 schema에 다음 필드를 넣고, P7/P8에 ranking sanity test를 추가한다.

- `score_source`
- `score_is_logprob`
- `length_penalty`
- `asr_cost`
- `asr_cost` 산출 규칙

### 6. N-best 유효성 판정 gate가 없다

파일/섹션:

- `docs/dev/specs/project-design.md` N-best 다양성
- `docs/wbs.md` P7 / P8

문제:

unique hypothesis count는 report만 하고, "이 정도면 N-best가 유효하다"는 판정 gate가 없다.

왜 중요한지:

후보가 거의 중복이면 WFST 합성의 이득이 낮은데 P10/P11까지 진행될 수 있다.

추천 수정 방향:

P7/P8 probe에 다음을 보고하고 P10 진입 조건 또는 risk flag를 둔다.

- unique count 분포
- domain oracle hit
- N-best oracle 개선 여부

### 7. evaluation input / gold manifest schema가 없다

파일/섹션:

- `docs/wbs.md` P9

문제:

evaluation metric은 많지만 reference/gold manifest schema가 없다.

왜 중요한지:

CER/WER, domain term accuracy, free-talk overcorrection은 gold text, split label, domain term annotation 없이는 재현성이 떨어진다.

추천 수정 방향:

P9에 evaluation input manifest schema를 추가한다.

예상 필드:

- `segment_id`
- `ref_text`
- `split`
- `is_free_talk`
- `domain_terms`
- `audio_ref`
- `allowed_rules`

### 8. overlapping rule tie-break 순서가 모호하다

파일/섹션:

- `docs/wbs.md` P5
- `docs/dev/specs/project-design.md` rule priority

문제:

WBS는 "긴 phrase 또는 priority"라고 되어 있어 tie-break 순서가 모호하다.

왜 중요한지:

overlapping rule 결과가 구현자마다 달라질 수 있다.

추천 수정 방향:

deterministic order를 고정한다.

예:

```text
length desc -> priority desc -> total cost -> stable rule_id
```

## Minor

### 1. top1 + correction 실행 방식이 명시돼 있지 않다

파일/섹션:

- `docs/dev/specs/project-design.md` evaluation
- `docs/wbs.md` P9

문제:

비교군 B인 "top1 + correction" 실행 방식이 명시돼 있지 않다.

왜 중요한지:

N-best 엔진에 rank0 하나만 넣는 방식인지 별도 top1 path인지 헷갈릴 수 있다.

추천 수정 방향:

B는 "N-best artifact를 rank0 단일 hypothesis로 truncate해서 같은 correction engine 사용"처럼 정의한다.

### 2. CT2 direct API와 faster-whisper wrapper 선택이 불명확하다

파일/섹션:

- `docs/wbs.md` P8

문제:

"CTranslate2 또는 faster-whisper"가 한 phase에 묶여 있지만 실제 API 노출 범위가 다를 수 있다.

왜 중요한지:

wrapper가 `sequences_ids` / `scores`를 충분히 노출하지 않으면 phase 완료 기준이 흔들린다.

추천 수정 방향:

P8 시작 시 primary target을 CT2 direct API인지 faster-whisper wrapper인지 먼저 결정하게 한다.

## Missing Questions

- current WBS SSOT는 계속 `docs/wbs.md`인가, 아니면 P0에서 `docs/ops/wbs.md`로 이동할 계획인가?
- MVP에서 `left_context` / `right_context`를 실제 지원할 것인가, 아니면 non-empty 값은 reject할 것인가?
- domain gate 입력은 무엇인가: 수동 segment metadata, 상담원/고객 채널, 스크립트 구간 label, config flag 중 무엇인가?
- 자유대화 허용 기준은 무엇인가: correction rate가 0이어야 하는가, 아니면 허용 threshold가 있는가?
- 이름 보호는 MVP에서 제외인가, 외부 annotation span만 지원인가, NER까지 해야 하는가?
- P10의 primary runtime은 HF인가, CT2/faster-whisper인가?
- N-best가 충분히 유효하다고 판단할 최소 oracle 개선 또는 unique 후보 기준이 있는가?

## Final Assessment

P0 진행 가능 여부: no, as written.

이유:

`docs/wbs.md`와 `docs/ops/wbs.md` 사이의 WBS SSOT 충돌을 먼저 정리해야 한다.

현재 design의 가장 큰 리스크:

context/boundary, obligatory/margin/domain gate 같은 safety semantics가 이름은 있지만 적용 우선순위와 실패 조건이 덜 고정돼 있다.

현재 WBS의 가장 큰 리스크:

phase별 산출물은 잘 나열돼 있지만 위험한 invariant들이 완료 기준에 빠져 있어, 나중 에이전트가 "통과한 것처럼 보이는" 구현을 만들 여지가 있다.
