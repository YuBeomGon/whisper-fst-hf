# WFST 도메인 성능 향상 가능성 리서치

날짜: 2026-06-26

문서 등급: feasibility audit report

검토 방식: subagent deep research

검토 대상:

- `docs/dev/specs/project-design.md`
- `docs/assets/aig_domain_data_context.md`

참고:

- `docs/assets/whisper_wfst_composition_research.md`

## 1. 질문

현재 설계한 방식, 즉 Whisper N-best hypothesis와 sequence score를 weighted acceptor로 만들고,
AIG 도메인 `hyp -> ref` correction WFST와 compose해 shortest path를 선택하는 방식이 실제로
AIG 보험 STT 도메인 성능을 향상시킬 가능성이 있는가?

또한 현재 설계와 데이터 이해 기준에서 버그, 제약, 미비한 gate, 과대가정은 무엇인가?

## 2. 결론

성능 향상 가능성은 **조건부로 있다**.

다만 이 방식은 "보험 도메인 일반 지식 주입"이 아니라, 실제 AIG 통화에서 반복 관측된
`hyp -> ref` 표면형 오류를 좁게 고치는 장치일 때만 유효하다.

가장 가능성이 높은 영역:

- 모델이 일관되게 다른 표면형을 내는 Category B 오류
- 도메인 term 표면형 교정
- support가 있고 자유대화 정상 표현 가능성이 낮은 phrase

가능성이 낮거나 위험한 영역:

- 모델이 아예 못 듣거나 N-best 안에도 없는 용어
- 음향적으로 누락된 구간
- score calibration이 안 된 N-best reranking
- 긴 script span 전체 교정
- 자유대화 또는 고객 채널에 넓게 적용되는 rule

신뢰도:

| 대상 | 판단 |
| --- | --- |
| vetted Category-B domain-term accuracy | medium |
| 전체 CER micro 개선 | low-to-medium |
| 자유대화까지 포함한 broad improvement | low |

따라서 구현 전 핵심은 "교정 엔진을 만드는 것"보다 먼저 **N-best targetability와 rule provenance를
검증하는 것**이다.

## 3. 왜 효과가 있을 수 있는가

### 3.1 N-best + score 구조는 top1 치환보다 정보가 많다

`docs/dev/specs/project-design.md`는 top1 텍스트 후처리가 아니라 N-best hypothesis와 score 기반 구조를
잡고 있다.

이 구조는 다음 경우에 top1 후처리보다 유리하다.

- top1은 틀렸지만 N-best 안에 정답 또는 교정 가능한 wrong form이 있는 경우
- 여러 candidate 중 ASR cost와 correction cost를 같이 보고 선택해야 하는 경우
- 같은 corrected output으로 여러 hypothesis가 모이는 경우

단, 이 장점은 N-best가 실제로 target 오류 주변의 plausible alternative를 포함할 때만 생긴다.

### 3.2 Identity-safe transducer 원칙은 올바른 방향이다

설계는 도메인 문장 acceptor나 강한 LM이 아니라 identity-safe correction transducer를 지향한다.

이 방향은 AIG 데이터에 중요하다. 보험 스크립트와 자유대화가 섞인 통화에서 도메인 문장 acceptor를
강하게 붙이면 일반 발화를 약관/스크립트 문장으로 끌고 갈 수 있다.

### 3.3 실제 `hyp -> ref` evidence가 있다

`docs/assets/aig_domain_data_context.md` 기준으로 다음 evidence source가 있다.

- `dictionary_registry.json`: applied `hyp_to_ref` entries 51개
- `aligned_segments.jsonl`: clean label `text`와 alignment용 `whisper_text` pair
- phrase-bias 실험의 Category B 분류

특히 registry에는 반복 support가 있는 표면형 교정 후보가 있다.

예:

```text
후유장애 -> 후유장해
급여상의 -> 급여상해
통합상의 -> 통합상해
염자 -> 염좌
라인화 -> 라이나
o건 -> 0건
```

이런 항목은 "도메인 지식을 생성"하는 문제가 아니라, 관측된 표면형 오류를 deterministic하게 되돌리는
문제라 WFST와 잘 맞는다.

### 3.4 Phrase-bias 실험이 역할 분리를 이미 보여준다

기존 phrase-bias 실험은 세 범주를 구분했다.

| Category | 모델 출력 양상 | 적절한 도구 |
| --- | --- | --- |
| A | 첫 token은 맞고 뒤를 흘림 | phrase bias |
| B | 일관된 다른 표면형으로 출력 | deterministic post-process / WFST |
| C | 전혀 안 뱉음 | finetune / stronger model / prompt |

WFST 프로젝트의 1차 대상은 Category B다. 이 범위로 좁히면 성능 향상 가능성은 있다.

## 4. 왜 실패할 수 있는가

### 4.1 N-best가 다양하지 않으면 top1 correction과 거의 같다

`beam_size=20`, `num_hypotheses=20`은 서로 다른 20문장을 보장하지 않는다.

후보가 거의 같은 문장, 공백, 조사, 문장부호 변이뿐이면 N-best + WFST는 top1 correction과 실질적으로
다르지 않다.

따라서 구현 전 다음을 봐야 한다.

- unique hypothesis count
- N-best oracle CER/WER
- domain term oracle hit
- target 오류 주변의 wrong form 또는 correct form 포함 여부

### 4.2 Corrected output은 Whisper가 직접 낸 문장이 아닐 수 있다

WFST composition은 다음 noisy-channel 구조다.

```text
P_Whisper(h | audio) * P_Correction(y | h)
```

이는 `P_Whisper(y | audio)`와 다르다. 즉 WFST가 만든 corrected `y`를 Whisper가 실제로 그 음성에서
선호한다는 보장은 없다.

따라서 correction cost가 너무 낮거나 margin이 약하면, 음향적으로 지지되지 않는 correction이 이길 수 있다.

### 4.3 Cost scale mismatch가 가장 큰 구현 리스크다

ASR cost와 correction cost의 scale이 맞지 않으면 shortest path가 의미 없는 순위를 낸다.

위험 요소:

- HF `transition_scores`와 `sequences_scores` 의미 차이
- CT2 score의 length penalty
- raw logprob인지 normalized score인지 불명확한 경우
- `lambda`, `corr_cost`, `keep_cost`, `margin`의 단위 불일치

성능 주장을 하려면 score sanity와 held-out calibration이 필요하다.

### 4.4 Rule leakage가 쉬운 구조다

`dictionary_registry.json`이나 alignment diff가 final eval 또는 judge normalization 결과에서 나온 것이라면,
그 rule로 같은 평가셋을 다시 평가하는 것은 자기충족적 개선이 될 수 있다.

특히 다음은 위험하다.

- final eval에서 발견한 오류를 rule로 만들고 같은 eval에서 개선 주장
- judge normalization에 유리한 표면형만 교정
- 긴 script span을 통째로 교정
- test transcript에서 domain term lexicon 추출

### 4.5 CER 개선 headroom은 제한적일 수 있다

기존 phrase-bias 결과에서 AIG finetune 모델은 base보다 훨씬 강했다.

보고된 수치:

| 구성 | CER | Domain recall |
| --- | ---: | ---: |
| base turbo | 0.1908 | 0.554 |
| AIG finetune | 0.108 | 0.792 |

이미 강한 finetune baseline을 기준으로 하면 WFST가 전체 CER micro를 크게 개선할 여지는 제한적일 수 있다.
WFST의 현실적 목표는 전체 CER 대폭 개선보다 domain term precision/recall과 regression-free correction이다.

## 5. 설계상 보완해야 할 점

### 5.1 Cost Calibration Contract

현재 설계는 목표식에 `lambda * CorrectionCost`를 두지만, 실제 composition 단계에서 lambda와 cost scale을
어떻게 적용할지 더 고정해야 한다.

필요한 contract:

- `asr_cost_policy`
- `score_source`
- `score_is_logprob`
- `length_penalty`
- `lambda`
- `corr_cost`
- `keep_cost`
- `margin`
- `cost_units`

필수 gate:

- finite non-negative `asr_cost`
- runtime rank와 cost 순서 일치율 >= 99%
- runtime별 ranking sanity test
- held-out calibration 전 final claim 금지

### 5.2 Margin Decision Semantics

`best_uncorrected_cost`가 어떤 후보 집합에서 계산되는지 명확해야 한다.

권장 정의:

- `best_identity_path`: correction rule을 적용하지 않은 best path
- `best_corrected_path`: correction rule 적용 후 best path
- `margin_pass = best_corrected_cost + margin < best_identity_cost`

obligatory rule도 final margin fail 시 revert할 수 있는지 결정해야 한다. 안전 관점에서는 domain gate와
margin이 obligatory rule보다 바깥에 있는 편이 낫다.

trace에는 다음을 모두 남긴다.

- best identity cost
- best corrected cost
- margin
- margin pass/fail
- revert 여부

### 5.3 Optional Rule Identity Bypass

optional rule은 다음 두 경로가 있어야 한다.

```text
wrong -> right / corr_cost
wrong -> wrong / keep_cost
```

하지만 일반 identity path가 `wrong -> wrong / 0`으로 우회하면 keep_cost가 무력화된다.

필수 gate:

- cdrewrite 기반 구현에서 property test
- optional rule이 identity path로 무료 우회되지 않는지 확인
- 실패하면 phrase trie 또는 leftmost-longest 직접 구현으로 제한

### 5.4 Boundary / Context

MVP에서 `left_context` / `right_context`는 reserved로 둔다. 이 결정은 안전하지만 recall을 낮출 수 있다.

보완해야 할 정책:

- 최소 rule length
- 금지 substring rule
- observed variant whitelist
- 조사 붙은 형태는 rule variant로 명시
- 전역 단일 음절 substitution 금지

### 5.5 Domain Gate Spec

현재 domain gate 개념은 있지만 입력과 fail-closed 정책이 부족하다.

권장 gate 입력:

- `channel`: `l`, `r`, `unknown`
- `is_script_span`
- `is_free_talk`
- `allowed_rules`
- optional `domain_gate_enabled`

권장 원칙:

- gate 정보가 없으면 fail-closed
- `_l` 상담원 채널과 script/domain segment에서만 rule set 활성화
- 자유대화는 default off 또는 high-confidence allowlist만 허용

### 5.6 Evaluation Group 정의

비교군은 더 분리해야 한다.

권장 비교군:

| Group | 의미 |
| --- | --- |
| `top1` | Whisper rank0 |
| `best_asr_cost_after_dedupe` | dedupe 후 ASR cost best |
| `nbest_oracle` | reference 기준 oracle. 실제 시스템 아님 |
| `top1_rules` | rank0 단일 hypothesis + correction |
| `nbest_rules` | N-best + correction |
| `nbest_rules_rescore` | optional teacher-force rescore |

이렇게 해야 N-best 자체의 이득과 rule correction의 이득을 분리할 수 있다.

### 5.7 Trace Schema v2

현재 trace는 기본 before/after/cost/rules 중심이다. 분석에는 부족하다.

추가 권장 필드:

- source hypothesis id / rank
- rule id / mode / priority
- rule matched span position
- domain gate input과 decision
- protected spans
- best identity cost
- best corrected cost
- margin result
- applied/reverted reason
- final output source: identity / corrected / fallback

## 6. 데이터 / 평가 리스크

### 6.1 Validation을 test로 쓰고 별도 valid가 없다

HF dataset은 train/validation 두 split만 있고 validation을 test로 운용한다.

위험:

- lambda, margin, rule cost를 validation에서 고르면 test leakage가 된다.

권장:

- source_wav 단위 calibration split을 별도 생성
- final test는 freeze 후 1회만 사용
- split 변경은 manifest로 기록

### 6.2 데이터 크기가 작다

HF validation은 424 chunks, 약 1.51h다. 운영 eval-of-record도 35 files다.

위험:

- CER 차이가 특정 파일 효과나 우연일 수 있다.

권장:

- paired bootstrap CI
- per-file win/loss
- date/source_wav stratified report
- 평균뿐 아니라 p50/p90/max error도 보고

### 6.3 30초 초과 validation chunk

validation에는 30초 초과 chunk 2건이 있다.

위험:

- Whisper segment behavior와 score가 다른 샘플과 달라진다.

권장:

- split/exclude policy를 평가 전에 고정
- long chunk를 별도 stratum으로 표시

### 6.4 `aligned_segments.whisper_text`는 현재 runtime 출력이 아닐 수 있다

`aligned_segments.jsonl`의 `whisper_text`는 alignment용 evidence다. 현재 구현할 HF/CT2 N-best runtime과
동일 모델, 동일 decoding 조건이 아닐 수 있다.

위험:

- rule이 현재 모델 오류와 맞지 않을 수 있다.

권장:

- current model/runtime N-best artifact에서 재현된 pair만 rule로 승격
- old alignment evidence는 seed 후보로만 사용

### 6.5 Alignment subset bias

alignment coverage summary 기준 audio coverage가 약 75%다.

위험:

- rule mining이 alignment가 잘 되는 구간에 치우친다.
- 어려운 자유대화/고객 발화에 대한 안전성이 과대평가된다.

권장:

- rule source coverage 보고
- unaligned/free-talk impact 별도 보고

### 6.6 Dictionary Registry Leakage

registry는 applied hyp->ref entries를 담고 있지만, 어디서 유래했는지 phase별로 분리해야 한다.

위험:

- final eval 유래 rule이면 leakage
- scorer normalization 맞춤 rule이면 raw 품질 개선이 아닐 수 있음
- 긴 span rule은 스크립트 memorization 위험

권장:

- final eval 유래 rule 금지
- provenance 필수
- span rule 기본 보류
- rule category별 allowlist

### 6.7 Judge Normalization False Confidence

judge normalization은 공백, 문장부호, `[INAUDIBLE]` 등을 제거한다.

위험:

- raw output 품질 악화가 judge CER에서 가려질 수 있다.
- spacing-only correction이 domain improvement처럼 보일 수 있다.

권장:

- raw CER
- judge CER
- raw domain-term exact
- normalized domain-term
- correction precision/recall
- overcorrection examples

### 6.8 운영 eval은 상담원 `_l` 중심이다

운영 eval-of-record는 상담원 `_l` 중심이다.

위험:

- 고객 채널 `_r`과 자유대화 safety claim은 약하다.

권장:

- `_l`, `_r`, script/free-talk stratified metrics 분리
- 고객 채널은 별도 gate 전에는 improvement claim 금지

## 7. 성능 향상 주장 전 필수 Gate

### 7.1 N-best Sanity Gate

필수 조건:

- `asr_cost`가 finite, non-negative
- runtime rank와 cost 순서 일치율 >= 99%
- unique hypothesis count 분포 보고
- duplicate 제거 후 후보 수 보고

### 7.2 Targetability Oracle Gate

보고해야 할 항목:

- 정답이 N-best 안에 있는 비율
- 안전 rule-trigger wrong form이 top1에 있는 비율
- 안전 rule-trigger wrong form이 N-best 안에 있는 비율
- top1+rules 대비 N-best+rules가 추가로 고칠 수 있는 비율

이 gate가 낮으면 N-best WFST의 추가 가치는 낮다.

### 7.3 Rule Promotion Gate

rule 승격 조건:

- final test에서 mined rule 금지
- 복수 source_wav support
- provenance 필수
- manual risk label
- span rule 기본 보류
- number/PII rule 기본 금지
- free-talk 정상 표현 가능성이 낮아야 함

### 7.4 Calibration Gate

필수 조건:

- `lambda`, `margin`, `corr_cost`, `keep_cost`는 held-out calibration에서만 선택
- final eval 전 config freeze
- calibration split과 final split의 source_wav 중복 금지

### 7.5 Correction Precision Gate

권장 threshold:

| Rule type | Precision |
| --- | ---: |
| obligatory | >= 98% |
| optional | >= 95% |

threshold 미달 rule은 disabled 또는 optional/high-margin으로 내려야 한다.

### 7.6 Free-talk Safety Gate

권장 threshold:

- free-talk correction rate <= 0.5% segments
- curated free-talk smoke에서 overcorrection 0건
- 예외가 있으면 explicit waiver 필요

### 7.7 Domain Metric Gate

권장 기준:

- targeted domain-term recall +2~5pp 이상
- precision drop <= 0.5pp
- rule별 contribution table 보고

### 7.8 CER Gate

권장 기준:

- judge `cer_micro` no regression
- 가능하면 paired bootstrap CI로 improvement 또는 non-regression 입증
- raw CER와 judge CER를 둘 다 보고

### 7.9 Final Ops Eval Gate

최종 claim은 운영 eval-of-record 전체 기준으로만 한다.

- 날짜 subset 금지
- partial eval 금지
- 35개 전체 eval
- 날짜별, 파일별 report 포함

## 8. 문서 / WBS에 추가할 항목

### 8.1 `docs/dev/specs/project-design.md`

추가 권장 섹션:

- Pre-implementation Research Gates
- Cost Calibration Contract
- Domain Gate Spec
- Rule Promotion Protocol
- Trace Schema v2
- Evaluation Group Definitions

### 8.2 `docs/wbs.md`

추가 또는 보강 권장 phase:

- Data / Rule Source Audit
- N-best Targetability Probe
- Rule Seed Audit
- Cost Calibration
- Frozen Final Evaluation

기존 P7/P8/P9/P10에 gate만 붙이는 것도 가능하지만, 성능 주장 리스크를 줄이려면 targetability probe와
rule seed audit은 별도 phase로 빼는 편이 더 안전하다.

### 8.3 새 research report

초기 구현 전 만들면 좋은 report:

```text
docs/reports/probes/nbest_targetability_probe.md
```

포함할 내용:

- top1 vs N-best oracle
- domain term oracle
- rule-trigger wrong form oracle
- unique hypothesis count
- score sanity
- targetability conclusion

## 9. 최종 판단

이 설계는 AIG 보험 STT의 반복적인 표면형 오인식, 특히 Category B 도메인 용어에는 개선 가능성이 있다.

하지만 현재 상태에서 곧바로 "도메인 성능이 향상될 것"이라고 주장하면 안 된다.

핵심 리스크:

1. N-best가 target 오류를 실제로 포함하지 않을 수 있다.
2. ASR cost와 correction cost scale이 맞지 않을 수 있다.
3. rule이 final eval에서 유래하면 leakage가 된다.
4. judge normalization이 raw 품질 변화를 가릴 수 있다.
5. 자유대화 overcorrection은 작은 rule에서도 발생할 수 있다.

따라서 다음 순서가 필요하다.

```text
data/rule source audit
-> N-best targetability probe
-> score sanity
-> rule promotion protocol
-> held-out calibration
-> frozen final evaluation
```

이 순서를 통과하면, WFST correction은 전체 STT 모델 개선 도구라기보다 **반복 관측된 도메인 표면형 오류를
추적 가능하게 줄이는 안전한 후처리 계층**으로 의미가 있다.
