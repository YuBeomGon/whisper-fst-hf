# Evaluation and Calibration Design

최종 갱신: 2026-06-26

문서 등급: operations policy

## 1. 목적

이 문서는 Whisper N-best + Correction WFST 구현 후 성능을 어떻게 평가하고, 어떤 변수를 바꿔가며
best configuration을 고를지 정의한다.

기준 문서:

- `docs/dev/specs/project-design.md`
- `docs/wbs.md`
- `docs/reports/audits/wfst-domain-feasibility-research.md`
- `docs/assets/aig_domain_data_context.md`

`docs/assets/**`는 read-only reference로 취급한다.

## 2. 핵심 원칙

이 프로젝트의 best config는 단순히 CER이 가장 낮은 config가 아니다.

우선순위는 다음이다.

1. 자유대화와 보호 span에서 과교정이 없어야 한다.
2. correction precision이 기준 이상이어야 한다.
3. targeted domain-term recall이 개선되어야 한다.
4. judge CER와 raw CER가 regression되지 않아야 한다.
5. latency와 artifact 크기가 운영 가능한 범위여야 한다.

따라서 "많이 고치는 config"가 아니라 "안전 조건을 통과한 것 중 도메인 개선이 가장 큰 config"를 best로
선택한다.

## 3. 비교군

평가는 최소한 아래 비교군을 사용한다.

| Group | Description | Purpose |
| --- | --- | --- |
| A | Whisper top1 | baseline |
| B | Whisper top1 + correction | top1 후처리만으로 가능한 개선 확인 |
| C | Whisper N-best only | N-best oracle / diversity 가치 확인 |
| D | Whisper N-best + Correction WFST | MVP target |
| E | optional N-best + WFST + teacher-force rescore | 후속 후보, MVP claim 제외 |

Group B는 별도 엔진을 만들지 않는다. N-best artifact를 rank0 단일 hypothesis로 truncate한 뒤 같은
correction engine을 통과시켜 비교한다.

## 4. 평가 split 정책

성능 주장을 하려면 tuning과 final evaluation을 분리한다.

| Split | Purpose | Rule |
| --- | --- | --- |
| synthetic | unit/integration 검증 | 실제 성능 주장 금지 |
| calibration | lambda, margin, rule policy 선택 | 변수 선택 가능 |
| free-talk safety | 과교정 확인 | safety gate 전용 |
| final eval-of-record | 최종 성능 주장 | config freeze 후 1회 평가 |

원칙:

- calibration split과 final split은 `source_wav` 단위로 겹치지 않는다.
- final eval에서 발견한 오류로 rule을 만들고 같은 final eval에 다시 적용하지 않는다.
- final eval 전 config, rule set, threshold, domain gate policy를 freeze한다.
- partial final eval 결과로 production-quality claim을 하지 않는다.
- 운영 eval-of-record를 사용할 경우 전체 35개 상담원 `_l` 파일 기준으로 보고한다.

## 5. Pre-implementation Targetability Probe

본격 tuning 전에 N-best가 실제로 correction value를 갖는지 먼저 확인한다.

보고 항목:

- normalized unique hypothesis count 분포
- top1 CER/WER
- N-best oracle CER/WER
- domain term oracle accuracy
- 정답 surface가 N-best 안에 있는 비율
- seed rule의 wrong surface가 top1에 있는 비율
- seed rule의 wrong surface가 N-best 안에 있는 비율

판단:

- N-best oracle이 top1보다 거의 낫지 않으면 N-best WFST의 추가 가치는 낮다.
- seed rule wrong surface가 top1에는 많고 N-best 추가 이득이 작으면 top1 correction을 우선 본다.
- wrong form도 correct form도 N-best에 거의 없으면 correction WFST로 개선하기 어렵다.

## 6. Sweep 대상 변수

### 6.1 Decode 변수

초기 후보:

| Variable | Candidate |
| --- | --- |
| `runtime` | `hf` |
| `num_beams` | `5`, `10`, `20` |
| `num_return_sequences` | `5`, `10`, `20`, 단 `num_return_sequences <= num_beams` |
| `length_penalty` | runtime 기본값, 필요 시 별도 실험 |

원칙:

- `num_beams=20`, `num_return_sequences=20`이 서로 다른 20문장을 보장하지 않는다.
- decode artifact를 먼저 만들고, correction sweep은 같은 artifact를 재사용한다.
- full cross product를 무작정 돌리지 않는다. 먼저 `num_beams=20`, `num_return_sequences=20`으로
  targetability를 보고, 필요할 때 작은 grid로 줄인다.

### 6.2 Cost 변수

초기 후보:

| Variable | Candidate |
| --- | --- |
| `lambda` | `0.1`, `0.3`, `1.0`, `3.0` |
| `margin` | `0.0`, `0.5`, `1.0`, `2.0` |
| `corr_cost` | rule class별 `0.05`, `0.1`, `0.3`, `1.0` |
| `keep_cost` | optional rule class별 `0.5`, `1.0`, `2.0`, `3.0` |

원칙:

- `asr_cost` scale sanity를 통과하기 전에는 cost sweep 결과를 성능 주장에 쓰지 않는다.
- `lambda`, `corr_cost`, `keep_cost`, `margin`은 calibration split에서만 선택한다.
- 최종 report에는 선택된 값뿐 아니라 탈락한 후보와 탈락 사유를 남긴다.

### 6.3 Rule policy 변수

초기 후보:

| Policy | Description |
| --- | --- |
| `safe_only` | support가 높고 자유대화 정상 표현 가능성이 낮은 rule만 활성화 |
| `safe_optional_medium` | safe rule + medium risk optional rule |
| `diagnostic_all` | 진단용 전체 rule, final claim 금지 |

승격 기준:

- final eval에서 mined rule 금지
- 복수 `source_wav` support
- provenance 필수
- manual risk label 필수
- 긴 span rule은 기본 보류
- number/PII rule은 기본 금지
- obligatory rule은 correction precision 기준을 더 높게 적용

### 6.4 Domain gate 변수

초기 후보:

| Policy | Description |
| --- | --- |
| `off` | correction disabled, identity-only |
| `allowed_rules_only` | manifest의 `allowed_rules`에 있는 rule만 허용 |
| `agent_channel_only` | 상담원 `_l` 채널에서만 허용 |
| `script_or_domain_span_only` | script/domain span에서만 허용 |

원칙:

- gate 정보가 없으면 fail-closed로 둔다.
- domain gate off이면 obligatory rule도 적용하지 않는다.
- 자유대화에서는 rule application rate가 거의 0이어야 한다.

## 7. Sweep 실행 순서

권장 순서:

1. synthetic fixture로 metric과 trace 계산이 맞는지 검증한다.
2. selected calibration audio에서 N-best artifact를 생성한다.
3. unique count, N-best oracle, domain oracle, seed rule wrong surface 비율을 먼저 보고한다.
4. targetability가 낮으면 cost sweep을 확대하지 않고 negative evidence로 기록한다.
5. safety-first rule set부터 correction sweep을 수행한다.
6. hard safety gate를 통과하지 못한 config는 즉시 탈락시킨다.
7. 통과 config에 대해서만 domain metric과 CER를 비교한다.
8. best config를 선택하고 config/rule/artifact checksum을 freeze한다.
9. frozen config로 final eval-of-record를 실행한다.
10. final 결과가 calibration과 반대이면 원인 분석 report를 남기고 claim을 낮춘다.

## 8. Hard Gate

아래 조건을 통과하지 못하면 best 후보가 될 수 없다.

| Gate | Required |
| --- | --- |
| Score sanity | finite non-negative `asr_cost`, runtime rank와 cost order 일치율 >= 99% |
| Manifest validity | `segment_id`, `audio_ref`, `source_wav`, `source_start`, `source_end`, `split`, `channel`, `is_script_span`, `is_free_talk`, `ref_text`, `domain_terms`, `allowed_rules` 검증 |
| Protection | protected span 내부 correction 0건 |
| Free-talk safety | curated free-talk smoke에서 overcorrection 0건 |
| Rule precision | obligatory >= 98%, optional >= 95% 권장 |
| CER safety | judge CER no regression, raw CER no regression 권장 |
| Leakage | final eval 유래 rule/config tuning 금지 |

## 9. Best 선택 규칙

Hard gate를 통과한 config만 후보로 둔다.

후보 사이의 정렬 기준:

1. targeted domain-term recall gain이 가장 큰 config
2. correction precision이 높은 config
3. judge CER와 raw CER가 더 낮은 config
4. 적용 rule 수가 적고 rule contribution이 명확한 config
5. latency가 낮은 config
6. 더 단순한 gate/rule policy를 쓰는 config

동률이면 더 보수적인 config를 선택한다.

선택된 config는 다음 정보를 함께 기록한다.

- config id
- model/runtime/decode config
- N-best artifact checksum
- rule CSV checksum
- rule policy
- domain gate policy
- `lambda`, `margin`, `corr_cost`, `keep_cost`
- selected reason
- rejected alternatives summary

## 10. Report Schema

calibration report는 최소한 다음 columns를 가진다.

```csv
config_id,split,runtime,model_id,num_beams,num_return_sequences,score_policy,lambda,margin,rule_policy,domain_gate_policy,rule_csv_sha256,artifact_sha256,segments,unique_hyp_mean,unique_hyp_p50,unique_hyp_p90,nbest_oracle_cer,domain_oracle_accuracy,judge_cer_micro,raw_cer_micro,domain_recall,domain_precision,correction_precision,correction_recall,overcorrection_rate,free_talk_correction_rate,free_talk_overcorrection_rate,decode_latency_avg_ms,fst_latency_avg_ms,status,reject_reason
```

per-rule contribution table은 별도로 둔다.

```csv
rule_id,wrong,right,mode,risk_label,support,applied,total_correct,total_wrong,precision,recall_contribution,cer_delta,free_talk_hits,status
```

## 11. 실패 해석

실패도 결과로 남긴다.

| Observation | Interpretation | Next action |
| --- | --- | --- |
| N-best oracle 개선 없음 | N-best 자체의 추가 정보가 적음 | top1 correction baseline 중심으로 전환 |
| rule-trigger wrong form 없음 | WFST가 붙을 입력 표면형이 없음 | rule 확대보다 extractor/model 개선 검토 |
| free-talk overcorrection 발생 | rule/gate가 넓음 | rule disable, optional 전환, margin 상향 |
| calibration만 개선되고 final에서 실패 | leakage 또는 overfit 가능성 | config freeze 원칙 재검토, split 재설계 |
| domain recall 상승 but precision 하락 | 과교정 | best 후보 탈락 또는 high-margin optional |
| judge CER 개선 but raw CER 악화 | normalization 착시 가능성 | raw output review와 rule별 기여 확인 |

## 12. WBS 반영 포인트

이 문서는 WBS의 P9, P10, P11에서 사용한다.

- P9: metric 계산, manifest validation, A/B/C/D report format
- P10: frozen artifact 기반 offline MVP run
- P11: calibration sweep, best config 선택, final eval 전 freeze

P11 완료 전에는 production-quality 성능 향상을 주장하지 않는다.
