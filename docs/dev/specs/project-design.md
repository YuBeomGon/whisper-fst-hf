# Whisper WFST Project Design

최종 갱신: 2026-06-26

## 1. 목적

이 프로젝트의 목적은 Whisper 계열 STT가 생성한 한국어 N-best 후보와 score를 사용해,
보험 도메인 오인식 phrase를 안전하게 교정하는 offline correction pipeline을 구현하는 것이다.

핵심 구조는 다음과 같다.

```text
audio
-> Whisper beam search
-> N-best hypotheses + sequence scores
-> weighted N-best acceptor A_x
-> correction WFST C
-> A_x o C
-> shortest path
-> corrected transcript + trace
```

이 문서는 현재 프로젝트 전체 설계의 기준 문서다. 초기 연구 원본은
`docs/assets/whisper_wfst_composition_research.md`이며, `docs/assets/**`는 수정하지 않는
reference 원본으로 취급한다.

## 2. 설계 원칙

### 2.1 N-best 중심

1차 구현은 top1 텍스트 후처리가 아니라 완성된 N-best hypothesis와 sequence score를 사용한다.

```text
y* = argmin_y min_h [ ASR_cost(h | audio) + lambda * CorrectionCost(h -> y) ]
```

- `h`: Whisper hypothesis
- `y`: correction output
- `ASR_cost`: Whisper score를 negative cost로 변환한 값
- `CorrectionCost`: correction WFST 경로 비용
- `lambda`: correction cost scale

beam=1 step별 vocab top-k mesh는 정확한 autoregressive lattice가 아니므로 1차 구현의 주력이 아니다.
필요하면 후속 실험으로 분리한다.

### 2.2 Identity-safe correction transducer

Correction WFST는 도메인 문장 acceptor가 아니라 correction transducer여야 한다.

허용되는 기본 동작은 다음이다.

```text
일반 텍스트: identity cost 0
명확한 오인식 phrase: wrong -> right correction
애매한 phrase: keep/correct branch + margin
```

즉, WFST가 자유발화를 보험 약관 문장처럼 강제로 끌고 가면 안 된다.

### 2.3 Evidence-first implementation

불확실한 의미를 추측하지 않는다. score 해석, rule 적용, overcorrection, runtime별 차이는
artifact와 report로 남긴다.

대용량 audio, model checkpoint, full prediction artifact는 repository에 넣지 않는다.
작은 manifest, report, config, test fixture만 version control 대상으로 둔다.

## 3. 범위

### 3.1 In scope

- Hugging Face Transformers Whisper N-best 추출
- N-best hypothesis artifact 저장/재사용
- weighted N-best acceptor 생성
- correction rule CSV schema
- phrase-level correction WFST 생성
- obligatory / optional correction mode
- priority, longest-match, margin 기반 overcorrection 방지
- 보호 span 처리
- composition + shortest path
- correction trace 생성
- CER/WER, domain term accuracy, N-best oracle, correction precision/recall, overcorrection rate 평가
- 자유대화 영향 평가

### 3.2 Out of scope for MVP

- step별 full vocab lattice 재구성
- diverse beam search
- log semiring posterior mass aggregation
- teacher-forcing rescore 기반 최종 재랭킹
- online streaming serving
- 도메인 LM 또는 약관 문장 acceptor를 강하게 붙이는 방식
- rule 자동 생성 또는 LLM 기반 correction
- CTranslate2/faster-whisper runtime integration

후속 phase에서 필요성이 확인되면 별도 WBS로 분리한다.

## 4. 주요 컴포넌트

### 4.1 Hypothesis extraction

Whisper runtime별 adapter가 audio를 받아 N-best를 반환한다.

공통 출력은 다음 개념을 따른다.

```python
Hypothesis(
    rank=int,
    token_ids=list[int],
    raw_text=str,
    normalized_text=str,
    score_source=str,
    score_is_logprob=bool,
    length_penalty=float | None,
    raw_logprob=float | None,
    decoder_score=float,
    asr_cost=float,
)
```

현재 PoC runtime은 HF Transformers Whisper다.

HF adapter는 `generate(..., num_beams=N, num_return_sequences=N, output_scores=True)`와
`compute_transition_scores()`를 사용한다.

score 의미가 불명확할 수 있으므로 artifact에는 raw score, normalized score, decode config, runtime,
model id를 함께 기록한다. score 관련 contract는 다음 필드를 포함한다.

- `score_source`: `hf_transition_scores`, `hf_sequences_scores` 등
- `score_is_logprob`: score가 log probability 성격인지 여부
- `length_penalty`: runtime에 적용된 length penalty 값
- `raw_logprob`: 복원 가능한 경우의 sequence log probability
- `decoder_score`: runtime이 직접 반환한 score
- `asr_cost`: composition에 사용할 non-negative cost

MVP에서 `asr_cost` 산출 규칙은 artifact 생성 시 명시적으로 기록한다. score sign이 불명확한 runtime은
ranking sanity test를 통과하기 전까지 production comparison에 사용하지 않는다.

### 4.2 Artifact IO

N-best artifact는 이후 WFST 비용 튜닝과 rule tuning을 음성 재전사 없이 반복하기 위한 기준 입력이다.

필수 필드:

- `segment_id`
- `model`
- `runtime`
- `decode_config`
- `hypotheses`
- `created_at`
- `audio_ref` 또는 source reference

artifact는 JSON 또는 JSONL로 저장한다. 대용량 artifact는 ignored output 경로에 두고, 작은 manifest와
checksum만 commit한다.

### 4.3 Normalization

한국어 텍스트는 기본적으로 Unicode NFC로 정규화한다.

MVP normalization은 다음만 수행한다.

- Unicode NFC
- runtime decode output의 leading/trailing whitespace 정리
- scoring용 duplicate key 생성

의미를 바꿀 수 있는 정규화는 기본값으로 넣지 않는다.

### 4.4 N-best acceptor

각 hypothesis를 하나의 weighted path로 만든다.

```text
path label = normalized_text
path weight = ASR_cost
```

ASR cost는 우선 다음 정책을 사용한다.

```text
if raw_logprob exists:
    ASR_cost = -raw_logprob
else:
    ASR_cost = -decoder_score
```

BPE token별 score를 문자나 음절로 억지 분배하지 않는다. hypothesis 전체 경로 cost로 둔다.
artifact에는 raw score와 함께 최종 `asr_cost`를 저장해 downstream composition이 score sign을 다시
해석하지 않게 한다.

### 4.5 Correction rule schema

기본 CSV schema:

```csv
rule_id,wrong,right,corr_cost,keep_cost,mode,left_context,right_context,priority,enabled
R001,손해보혐,손해보험,0.1,3.0,optional,,,100,true
R002,알릴 의모,알릴 의무,0.1,,obligatory,,,100,true
```

필드 의미:

| Field | Meaning |
| --- | --- |
| `rule_id` | trace용 stable id |
| `wrong` | ASR 오인식 phrase |
| `right` | 교정 phrase |
| `corr_cost` | correction branch cost |
| `keep_cost` | optional mode에서 keep branch cost |
| `mode` | `obligatory` 또는 `optional` |
| `left_context` | reserved for future boundary/context support |
| `right_context` | reserved for future boundary/context support |
| `priority` | 겹치는 rule 처리 우선순위 |
| `enabled` | rule 활성화 여부 |

MVP에서는 `left_context`와 `right_context`의 non-empty 값을 지원하지 않는다. rule loader는 non-empty
context를 만나면 silent ignore하지 않고 validation error를 낸다. 경계 처리는 우선 실제 관측된 phrase
variant를 rule로 명시하는 방식으로 제한한다.

### 4.6 Correction WFST

Correction WFST는 다음을 표현한다.

```text
input: ASR hypothesis text
output: corrected text
weight: correction cost
```

MVP rule 처리 원칙:

- 일반 identity는 cost 0
- phrase correction은 phrase 전체 context에서만 적용
- 전역 단일 문자 substitution은 금지
- 겹치는 rule은 deterministic order로 처리
- optional rule은 keep/correct branch를 명시
- identity path가 optional rule의 keep cost를 무료로 우회하지 않는지 unit test로 검증

겹치는 rule tie-break 순서:

```text
length desc -> priority desc -> total cost -> stable rule_id
```

### 4.7 Composition

합성 결과에서 shortest path를 선택한다.

```text
Z = A_x o C
best = shortest_path(Z)
output = project_output(best)
```

composition 결과가 비어 있으면 안전 fallback으로 best ASR hypothesis를 반환하고 trace에 failure reason을 남긴다.

### 4.8 Trace

모든 correction 결과는 최소한 다음 정보를 남긴다.

```json
{
  "segment_id": "call-001-seg-003",
  "source_hypothesis_rank": 0,
  "before": "손해보혐 가입에 동의하십니까",
  "after": "손해보험 가입에 동의하십니까",
  "asr_cost": 3.8,
  "correction_cost": 0.2,
  "total_cost": 4.0,
  "rules": [
    {
      "rule_id": "R001",
      "wrong": "손해보혐",
      "right": "손해보험"
    }
  ]
}
```

trace는 debugging뿐 아니라 overcorrection evaluation의 핵심 입력이다.

## 5. 도메인 Correction WFST와 자유대화 성능 하락 리스크

Correction WFST가 도메인 문장 acceptor처럼 동작하면 자유대화 성능을 떨어뜨릴 수 있다.
예를 들어 강한 보험 약관 LM이나 문장 acceptor를 붙이면 일반 발화를 약관 문장으로 끌고 갈 위험이 있다.

MVP의 안전 기준은 다음이다.

- Correction graph는 identity-safe transducer여야 한다.
- 자유대화 segment에서는 rule 적용률이 거의 0이어야 한다.
- 명확한 도메인 오인식 phrase만 correction 대상으로 삼는다.
- 애매한 rule은 `optional` mode와 margin 조건을 사용한다.
- 상담원 채널, 스크립트 구간, 약관 낭독 구간 등에서만 domain gating을 켤 수 있어야 한다.
- domain gate가 꺼진 경우에는 identity path만 허용하거나 correction rule set을 비활성화할 수 있어야 한다.
- 자유대화 evaluation set에서 correction application rate와 overcorrection rate를 별도로 측정한다.

따라서 correction 효과 평가는 보험 도메인 발화 성능만 보지 않는다. 반드시 자유대화 residual risk를 함께 본다.

## 6. Beam size / num hypotheses와 N-best 다양성 문제

HF 기준 `num_beams=20`, `num_return_sequences=20`은 서로 다른 문장 20개를 보장하지 않는다.

ASR N-best의 목적은 다양한 문장을 생성하는 것이 아니다. 대부분 후보가 비슷해도 정상이며, 중요한 것은
오인식 구간 주변의 plausible alternative가 살아 있는지다.

MVP 정책:

- 후보가 공백, 문장부호, 조사 정도만 다를 수 있음을 정상으로 본다.
- Unicode normalization 후 중복 제거를 수행한다.
- 중복된 normalized text는 가장 낮은 ASR cost hypothesis만 유지한다.
- unique hypothesis 수가 요청한 `num_return_sequences`보다 적을 수 있음을 artifact와 report에 기록한다.
- diverse beam search는 1차 구현에 넣지 않는다.
- N-best의 가치는 N-best oracle CER/WER와 domain term oracle accuracy로 판단한다.
- P10 end-to-end run 전에 unique count 분포, domain oracle hit, N-best oracle 개선 여부를 risk gate로 확인한다.

N-best가 비슷해 보이더라도 target domain 오류가 top-k 내부에서 교정 가능한 형태로 살아 있으면 WFST 합성의
가치가 있다.

만약 N-best oracle 개선이나 domain oracle hit가 전혀 없으면 P10은 correction 효과 검증이 아니라
negative evidence run으로만 해석한다. 이 경우 P11 calibration으로 바로 넘어가지 않는다.

## 7. Overcorrection safety

MVP는 다음 safety layer를 둔다.

### 7.1 Safety decision order

MVP correction 적용 순서는 다음으로 고정한다.

```text
normalize/dedupe
-> protect spans
-> domain gate
-> build N-best acceptor
-> compose with correction WFST
-> shortest path
-> margin decision
-> restore protected spans
-> trace
```

domain gate가 off이면 obligatory rule도 적용하지 않는다. 이 경우 correction graph는 identity-only로
동작하거나 correction rule set을 비활성화한다. margin은 최종 corrected path와 uncorrected path의
cost 비교에 적용한다.

### 7.2 Margin

교정 후보가 원본보다 충분히 좋아야 적용한다.

```text
best_corrected_cost + margin < best_uncorrected_cost
```

차이가 작으면 원문을 유지한다.

### 7.3 Protected spans

교정 전 다음 span은 placeholder로 보호한다.

- 전화번호
- 주민번호
- 계좌번호
- 카드번호
- 증권번호
- 금액
- 날짜
- URL
- 영문 코드

이름은 MVP에서 NER로 자동 탐지하지 않는다. 이름 보호가 필요하면 upstream metadata나 외부 annotation으로
span을 주입받는 `external protected span`만 지원한다.

### 7.4 Risky rules

둘 다 실제로 가능한 도메인 단어인 경우 고위험 rule로 본다.

예:

```text
보험금 -> 보험료
고객 -> 계약
상해 -> 상회
```

고위험 rule은 기본 disabled 또는 optional + high margin으로만 허용한다.

## 8. Evaluation

평가와 calibration의 상세 정책은 `docs/ops/evaluation-calibration-design.md`를 따른다.
여기에는 split 정책, sweep 변수, hard gate, best config 선택 규칙, report schema를 둔다.

비교군:

| Group | Description |
| --- | --- |
| A | Whisper top1 |
| B | Whisper top1 + correction. N-best artifact를 rank0 단일 hypothesis로 truncate한 뒤 같은 correction engine을 사용 |
| C | Whisper N-best only |
| D | Whisper N-best + correction WFST |
| E | optional N-best + WFST + teacher-force rescore |

핵심 metric:

| Metric | Meaning |
| --- | --- |
| CER/WER | 전체 전사 정확도 |
| Domain term accuracy | 보험 용어 정확도 |
| N-best oracle CER/WER | N개 후보 중 정답에 가장 가까운 후보 성능 |
| Domain term oracle accuracy | N-best 안에 도메인 정답 후보가 있는지 |
| Correction precision | 적용 correction 중 실제 정답 비율 |
| Correction recall | correction 가능한 오류 중 고친 비율 |
| Overcorrection rate | 맞던 텍스트를 틀리게 바꾼 비율 |
| Free-talk correction rate | 자유대화에서 rule이 적용된 비율 |
| Free-talk overcorrection rate | 자유대화에서 발생한 잘못된 correction 비율 |
| Rule coverage | rule이 커버한 오류 비율 |
| Unique hypothesis count | dedupe 후 남은 후보 수 |
| Decode latency | Whisper N-best 비용 |
| FST latency | graph build/compose 비용 |

Unavailable metric은 0으로 처리하지 않고 `not_applicable`로 기록한다.

Evaluation input manifest는 최소한 다음 필드를 가진다.

- `segment_id`
- `audio_ref`
- `split`
- `ref_text`
- `is_free_talk`
- `domain_terms`
- `allowed_rules`

`ref_text`가 없는 segment는 CER/WER 또는 domain term accuracy의 denominator에 넣지 않는다.

## 9. Expected project structure

실제 scaffold는 WBS의 초기 phase에서 만든다. 목표 구조는 다음이다.

```text
whisper-fst-hf/
  AGENTS.md
  pyproject.toml
  configs/
    hf.yaml
    correction.yaml
  data/
    correction_rules.csv
  docs/
    wbs.md
    assets/
      whisper_wfst_composition_research.md
    ops/
      governance.md
      coding-conventions.md
      environment.md
      phase-loop.md
      schema.md
      evaluation.md
    dev/
      specs/
        project-design.md
      plans/
    reports/
      audits/
      probes/
      experiments/
    reviews/
      design/
      code/
  src/
    whisper_wfst/
      types.py
      normalize.py
      artifact_io.py
      rule_io.py
      nbest_acceptor.py
      correction_wfst.py
      compose.py
      trace.py
      hf_extractor.py
      evaluate.py
  tests/
```

## 10. Verification strategy

MVP 필수 테스트:

1. `손해보혐 -> 손해보험`
2. 문장 나머지는 identity로 보존
3. `혐오`가 `험오`로 바뀌지 않음
4. `보혐`과 `손해보혐`이 겹칠 때 긴 phrase 우선
5. 등록한 변형만 처리
6. 길이가 다른 correction 처리
7. 동일 corrected output으로 여러 N-best path가 모일 때 lowest total cost 선택
8. rule 미적용 시 lowest ASR cost hypothesis 유지
9. composition 결과 없음 fallback
10. NFC/NFD 한글 정규화
11. optional rule에서 identity free bypass 금지
12. 자유대화 fixture에서 rule 적용률 0 또는 기대 범위
13. normalized duplicate hypothesis dedupe

기본 검증 명령은 scaffold phase에서 확정한다. 예상 기본값은 다음이다.

```bash
uv run --group dev ruff check .
uv run --group dev pytest
git diff --check
```

## 11. Key risks

| Risk | Mitigation |
| --- | --- |
| Pynini/OpenFST 설치 난이도 | 초기에 dependency feasibility phase를 둔다 |
| HF score 의미 차이 | artifact에 raw metadata 기록, lambda calibration 분리 |
| Domain rule overcorrection | optional rule, margin, protected spans, free-talk eval |
| Beam 후보 중복 | normalized dedupe, unique count report |
| 긴 문장 identity cost bias | identity cost 0 유지 |
| Rule priority ambiguity | longest/priority policy를 test로 고정 |
| Large artifact repository pollution | outputs ignored, committed manifest/report only |

## 12. Initial implementation direction

초기 구현은 다음 순서가 안전하다.

1. governance와 scaffold를 먼저 고정한다.
2. FST dependency feasibility를 확인한다.
3. 음성 없이 synthetic N-best artifact로 composition engine을 만든다.
4. correction safety와 trace를 붙인다.
5. HF extractor를 붙여 실제 N-best artifact를 만든다.
6. HF N-best targetability를 검증한다.
7. evaluation harness로 효과와 자유대화 risk를 같이 본다.
