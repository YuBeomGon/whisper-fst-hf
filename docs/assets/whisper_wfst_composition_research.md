# Whisper 출력 확률/N-best와 Correction WFST 합성 설계 문서

최종 갱신: 2026-06-26  
목적: Codex가 바로 구현할 수 있도록, **Whisper 출력 후보와 오인식→정인식 Correction WFST를 합성하는 방식**을 정리한다.

---

## 0. 핵심 요약

최초 구현은 다음 구조가 가장 안전하다.

```text
음성
→ Whisper beam search
→ 완성된 N-best hypothesis + 각 hypothesis score
→ Weighted N-best Acceptor A_x
→ Correction WFST C
→ A_x ∘ C
→ shortest path
→ corrected transcript
```

중요한 결론은 다음이다.

```text
1. top1 텍스트만 후처리하는 것도 가능하다.
2. 하지만 확률을 쓰려면 완성된 N-best hypothesis와 sequence score를 쓰는 것이 가장 깔끔하다.
3. beam=1에서 매 step vocab top20을 저장해 T×20 그래프를 만드는 것은 가능하지만, 정확한 Whisper lattice는 아니다.
4. 구현 1차 목표는 N-best weighted acceptor + correction WFST composition이다.
5. HF Transformers와 CTranslate2 모두 N-best + score 추출 경로가 있다.
```

최종 목표 식은 다음처럼 볼 수 있다.

```text
y* = argmin_y min_h [ ASR_cost(h | audio) + λ × CorrectionCost(h → y) ]
```

여기서:

- `h`: Whisper가 낸 후보 transcript
- `y`: 교정 후 transcript
- `ASR_cost`: Whisper hypothesis score를 negative log cost로 변환한 값
- `CorrectionCost`: 오인식→정인식 WFST 경로 비용
- `λ`: 교정 비용 scale

---

## 1. 왜 top-n / n-best 중심으로 가야 하는가

대화 중 세 가지 후보 구조가 나왔다.

| 구조 | 의미 | 1차 구현 추천 |
|---|---|---|
| top1 text 후처리 | Whisper가 낸 최종 문장 하나만 교정 | 가능하지만 확률 활용 약함 |
| beam=1 step별 vocab top20 | 각 decoding step마다 top20 token 확률 저장 | 실험 가능하지만 정확한 lattice 아님 |
| beam search N-best | 실제 beam search로 완성된 N개 hypothesis와 score 저장 | **추천** |

### 1.1 top1 text 방식

```text
Whisper top1 text
→ input acceptor
→ correction WFST
→ corrected text
```

장점:

```text
빠름
음성 재전사 없이 텍스트만으로 테스트 가능
구현 쉬움
교정 로그 분석 쉬움
```

단점:

```text
Whisper 확률을 거의 쓰지 못함
top1에 없는 대안 후보를 살릴 수 없음
```

### 1.2 beam=1 step별 vocab top20 방식

Whisper greedy decoding 중 각 step에서 vocab top20을 저장한다.

```text
step 1: top20 token + logprob
step 2: top20 token + logprob
...
```

이를 다음과 같은 WFSA로 만들 수 있다.

```text
state 0 → state 1: step1 top20 arcs
state 1 → state 2: step2 top20 arcs
state 2 → state 3: step3 top20 arcs
...
```

하지만 이 방식은 **정확한 Whisper lattice가 아니다.** 이유는 Whisper가 autoregressive 모델이기 때문이다.

Whisper 확률은 다음 형태다.

```text
P(y_t | audio, y_<t)
```

예를 들어 greedy prefix가 다음과 같았다고 하자.

```text
손해보혐
```

그 다음 step에서 저장된 확률은:

```text
P(next token | audio, "손해보혐")
```

이다. 그런데 WFST가 중간에서:

```text
손해보혐 → 손해보험
```

으로 바꾸면, 다음 step 확률은 원래:

```text
P(next token | audio, "손해보험")
```

이어야 한다. 저장된 벡터와 다르다.

따라서 step별 top20 mesh는 다음 용도로는 가능하다.

```text
국소 token 후보 분석
한두 token substitution 실험
confidence 분석
posterior mesh 실험
```

하지만 1차 구현의 주력으로 쓰기에는 불안정하다.

### 1.3 N-best 방식

Whisper beam search로 완성된 N개 hypothesis를 얻는다.

```text
h1 = 손해보혐 가입에 동의하십니까, score = -3.8
h2 = 손해보험 가입에 동의하십니까, score = -4.2
h3 = 손해보현 가입에 동의하십니까, score = -5.1
```

이 N개는 실제 beam search 과정에서 각 prefix별 확률을 따라 생성된 완성 후보들이다. 그래서 각 hypothesis의 sequence score는 해당 sequence에 대해 일관적이다.

추천 1차 구현은 이것이다.

```text
Whisper N-best + sequence score
→ weighted acceptor
→ correction WFST와 compose
```

---

## 2. 전체 구조

### 2.1 그래프 2개를 만든다

필요한 그래프는 두 개다.

```text
A_x = Whisper N-best weighted acceptor
C   = Correction WFST
```

합성:

```text
Z = A_x ∘ C
```

최종 출력:

```text
best = shortest_path(Z)
output = project_output(best)
```

### 2.2 Whisper N-best weighted acceptor

각 hypothesis를 하나의 path로 만든다.

예:

```text
h1: 손해보혐 가입에 동의하십니까 / cost 3.8
h2: 손해보험 가입에 동의하십니까 / cost 4.2
h3: 손해보현 가입에 동의하십니까 / cost 5.1
```

각 cost는 보통 다음처럼 둔다.

```text
ASR_cost = - raw_logprob
```

또는 runtime이 normalized score만 줄 경우:

```text
ASR_cost = - normalized_score
```

단, normalized score는 length penalty가 반영됐을 수 있으므로 λ 튜닝이 필요하다.

### 2.3 Correction WFST

Correction WFST는 다음을 표현한다.

```text
입력: ASR 후보 문자열
출력: 정인식/표준 문자열
weight: 교정 비용
```

예:

```text
손해보혐 → 손해보험 / cost 0.1
납임 → 납입 / cost 0.1
알릴 의모 → 알릴 의무 / cost 0.1
```

---

## 3. `손해보혐 → 손해보험`을 WFST로 정확히 표현하기

### 3.1 phrase pair

원본 pair:

```text
wrong = 손해보혐
right = 손해보험
```

음절 단위로 풀면:

```text
입력: 손 해 보 혐
출력: 손 해 보 험
```

Correction path:

```text
q0 -- 손:손 / 0.0 --> q1
q1 -- 해:해 / 0.0 --> q2
q2 -- 보:보 / 0.0 --> q3
q3 -- 혐:험 / 0.1 --> q4
```

여기서 중요한 점:

```text
혐 → 험
```

은 전역 규칙이 아니다. 반드시 `손 해 보`를 본 뒤의 상태에서만 허용된다.

즉 다음처럼 만들면 안 된다.

```text
전역 규칙: 혐 → 험
```

이러면 `혐오 → 험오` 같은 과교정이 생긴다.

### 3.2 identity 처리 주의

일반 문자는 그대로 지나가야 한다.

```text
고 → 고
객 → 객
님 → 님
공백 → 공백
...
```

하지만 Correction WFST 설계에서 매우 중요한 함정이 있다.

초기에 논의했던:

```text
일반 identity cost = 1.0
phrase correction cost = 0.1
```

은 테스트용으로는 직관적이지만, 최종 설계로는 주의가 필요하다.

문장이 길어질수록 identity 비용이 불필요하게 커진다.

```text
10글자 = identity cost 10
100글자 = identity cost 100
```

따라서 일반적으로는:

```text
일반 identity cost = 0.0
```

이 맞다.

그 대신 phrase가 매칭됐을 때만 local keep/correct branch를 둔다.

### 3.3 두 가지 교정 모드

#### 모드 A: obligatory correction

`손해보혐`이라는 문자열이 정상 표현일 가능성이 사실상 없다면, 그대로 유지 경로를 두지 않는다.

```text
손해보혐 → 손해보험 / 0.1
```

이 경우 해당 phrase가 매칭되면 반드시 교정된다.

#### 모드 B: optional weighted correction

애매한 경우에는 keep와 correct를 둘 다 둔다.

```text
손해보혐 → 손해보험 / corr_cost 0.2
손해보혐 → 손해보혐 / keep_cost 2.0
```

이때 일반 identity가 phrase match를 0 비용으로 우회하지 못하게 해야 한다. 구현상 다음 중 하나가 필요하다.

```text
context-dependent rewrite
leftmost-longest rewrite
phrase trie 기반 직접 구현
rule priority
local branch 강제
```

---

## 4. Correction rule CSV 스키마

단순한 `wrong,right`보다 다음 스키마가 좋다.

```csv
rule_id,wrong,right,corr_cost,keep_cost,mode,left_context,right_context,priority,enabled
R001,손해보혐,손해보험,0.1,3.0,optional,,,100,true
R002,알릴 의모,알릴 의무,0.1,3.0,obligatory,,,100,true
R003,보혐료,보험료,0.2,2.0,optional,,,90,true
```

필드 설명:

| 필드 | 의미 |
|---|---|
| rule_id | 로그 추적용 ID |
| wrong | ASR 오인식 표현 |
| right | 정인식/표준 표현 |
| corr_cost | 교정 경로 비용 |
| keep_cost | 유지 경로 비용 |
| mode | obligatory 또는 optional |
| left_context | 좌측 문맥 제약 |
| right_context | 우측 문맥 제약 |
| priority | 겹치는 규칙 처리 우선순위 |
| enabled | 규칙 활성화 여부 |

---

## 5. 경계와 문맥

전역 substring 교정은 위험하다.

예:

```text
보혐 → 보험
```

을 무조건 적용하면 의도하지 않은 문자열 내부에서도 바뀔 수 있다.

따라서 가능한 경우 경계를 둔다.

```text
LEFT  = BOS | 공백 | 문장부호
RIGHT = EOS | 공백 | 문장부호 | 조사
```

한국어는 조사가 붙는다.

```text
손해보혐에 → 손해보험에
손해보혐을 → 손해보험을
```

처음에는 실제 관측된 pair 중심으로 가는 것이 안전하다.

```text
손해보혐 → 손해보험
손해보혐에 → 손해보험에
손해보혐을 → 손해보험을
```

나중에 조사 처리를 일반화한다.

---

## 6. 겹치는 규칙 처리

예:

```text
보혐 → 보험
손해보혐 → 손해보험
```

입력:

```text
손해보혐
```

원하는 결과:

```text
손해보험
```

짧은 규칙이 먼저 적용되면 전체 phrase 규칙을 깨뜨릴 수 있다. 따라서 다음 정책이 필요하다.

```text
1. 긴 phrase 우선
2. priority 높은 rule 우선
3. 전체 경로 cost가 낮은 쪽 선택
4. leftmost-longest rewrite
```

MVP에서는:

```text
길이 내림차순 + priority 내림차순
```

으로 컴파일하고 unit test로 고정한다.

---

## 7. 길이가 다른 교정

WFST에서는 epsilon을 사용한다.

예:

```text
가입동의 → 가입에 동의
```

입력/출력 길이가 다르다.

개념적 arc:

```text
가:가
입:입
ε:에
ε:공백
동:동
의:의
```

삭제는:

```text
불필요음절:ε
```

로 표현한다.

삽입/삭제는 substitution보다 과교정 위험이 높으므로 비용을 더 높게 둔다.

---

## 8. N-best acceptor 만들기

### 8.1 데이터 구조

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Hypothesis:
    rank: int
    token_ids: list[int]
    raw_text: str
    normalized_text: str
    raw_logprob: float | None
    decoder_score: float
```

### 8.2 JSON artifact 예

```json
{
  "segment_id": "call-001-seg-0003",
  "model": "openai/whisper-large-v3",
  "runtime": "transformers",
  "decode_config": {
    "beam_size": 20,
    "num_hypotheses": 20,
    "length_penalty": 1.0,
    "language": "ko",
    "task": "transcribe"
  },
  "hypotheses": [
    {
      "rank": 0,
      "token_ids": [123, 456],
      "raw_text": "손해보혐 가입에 동의하십니까",
      "normalized_text": "손해보혐 가입에 동의하십니까",
      "raw_logprob": -3.8,
      "decoder_score": -0.31
    }
  ]
}
```

이 artifact를 저장해두면 이후 WFST 규칙과 비용 튜닝에는 음성이 필요 없다.

단, 이미 top1 텍스트만 있고 N-best/score가 없다면 음성으로 Whisper를 다시 실행해야 한다.

### 8.3 Pynini 의사 코드

```python
import unicodedata
import pynini
from pynini.lib import pynutil


def normalize_korean(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def build_nbest_acceptor(hypotheses):
    paths = []

    with pynini.default_token_type("utf8"):
        for hyp in hypotheses:
            text = normalize_korean(hyp.normalized_text)

            if hyp.raw_logprob is not None:
                asr_cost = -hyp.raw_logprob
            else:
                asr_cost = -hyp.decoder_score

            path = pynini.accep(text)
            path = pynutil.add_weight(path, asr_cost)
            paths.append(path)

        return pynini.union(*paths).optimize()
```

중요:

```text
N-best path의 weight는 hypothesis 전체 cost로 붙인다.
BPE token별 cost를 음절별로 억지 분배하지 않는다.
```

---

## 9. Correction WFST 만들기

Pynini 기반 개념 코드:

```python
from dataclasses import dataclass
import pynini
from pynini.lib import pynutil


@dataclass(frozen=True)
class CorrectionRule:
    rule_id: str
    wrong: str
    right: str
    corr_cost: float
    keep_cost: float | None
    obligatory: bool
    priority: int = 0


def make_local_mapping(rule: CorrectionRule):
    corrected = pynutil.add_weight(
        pynini.cross(rule.wrong, rule.right),
        rule.corr_cost,
    )

    if rule.obligatory:
        return corrected

    kept = pynutil.add_weight(
        pynini.cross(rule.wrong, rule.wrong),
        rule.keep_cost,
    )

    return pynini.union(corrected, kept).optimize()


def build_correction_wfst(rules, alphabet):
    with pynini.default_token_type("utf8"):
        # 실제 구현에서는 priority/longest-match/context 처리를 추가해야 함.
        mappings = pynini.union(
            *(make_local_mapping(rule) for rule in rules if rule.enabled)
        ).optimize()

        sigma = pynini.union(*alphabet)
        sigma_star = sigma.closure().optimize()

        return pynini.cdrewrite(
            mappings,
            "",
            "",
            sigma_star,
        ).optimize()
```

주의:

```text
cdrewrite가 원하는 optional/obligatory semantics로 동작하는지 반드시 unit test 필요.
identity가 무료로 rule을 우회하지 않는지 검증해야 함.
```

규칙 수가 적고 완전 통제가 필요하면 `pywrapfst.VectorFst`로 phrase trie를 직접 만드는 것도 가능하다.

---

## 10. 합성과 shortest path

```python
def apply_correction(nbest_acceptor, correction_wfst):
    lattice = pynini.compose(nbest_acceptor, correction_wfst)

    if lattice.start() == pynini.NO_STATE_ID:
        raise RuntimeError("Composition produced no valid path")

    best_joint_path = pynini.shortestpath(
        lattice,
        nshortest=1,
    ).optimize()

    best_output = pynini.project(
        best_joint_path,
        project_type="output",
    ).optimize()

    return best_output.string()
```

개념:

```text
A_x = Whisper N-best weighted acceptor
C   = correction WFST
Z   = A_x ∘ C
best = shortest_path(Z)
output = project_output(best)
```

---

## 11. 동일 출력으로 여러 경로가 모이는 경우

예:

```text
h1 = 손해보혐 → 손해보험
h2 = 손해보험 → 손해보험
h3 = 손해보헙 → 손해보험
```

세 경로 모두 출력은:

```text
손해보험
```

이다.

MVP에서는 tropical shortest path 방식으로:

```text
가장 낮은 total cost 경로 하나
```

를 선택하면 된다.

나중에 같은 output으로 모이는 확률 질량을 합치고 싶다면 log semiring 기반 log-sum-exp 집계를 고려할 수 있다. 하지만 초기 구현은 복잡해지므로 권장하지 않는다.

---

## 12. 교정된 텍스트의 Whisper 확률 해석

합성 모델은 다음 noisy-channel 형태다.

```text
음성 → Whisper hypothesis h → Correction WFST output y
```

즉:

```text
P_Whisper(h | audio) × P_C(y | h)
```

를 보는 것이다.

이것은 교정된 `y`를 Whisper가 직접 생성했을 때의 확률:

```text
P_Whisper(y | audio)
```

과 다르다.

고도화하려면:

```text
A_x ∘ C
→ corrected candidate M개 생성
→ 각 candidate를 Whisper teacher forcing으로 다시 점수화
→ 최종 재선택
```

을 추가할 수 있다.

하지만 1차 구현에서는 N-best+WFST shortest path로 충분하다.

---

## 13. Hugging Face Transformers 적용

### 13.1 N-best 추출

HF `generate()`에서 다음을 사용한다.

```python
outputs = model.generate(
    input_features=input_features,
    language="ko",
    task="transcribe",
    return_timestamps=False,
    do_sample=False,
    num_beams=20,
    num_return_sequences=20,
    return_dict_in_generate=True,
    output_scores=True,
)

texts = processor.batch_decode(
    outputs.sequences,
    skip_special_tokens=True,
)
```

### 13.2 transition score 복원

```python
transition_scores = model.compute_transition_scores(
    outputs.sequences,
    outputs.scores,
    outputs.beam_indices,
    normalize_logits=True,
)

raw_logprob = transition_scores.sum(dim=1)
asr_cost = -raw_logprob
```

확인할 것:

```text
forced language/task token이 score에 포함되는지
EOS 이후 padding score 처리
length penalty 적용 여부
sequences_scores와 raw_logprob의 관계
beam_indices 존재 여부
```

### 13.3 HF 주의점

Whisper는 long-form 처리에서 segment 단위 generation output 구조가 다를 수 있다. 먼저 30초 이하 단일 segment에서 검증한다.

권장 startup test:

```text
num_beams=5
num_return_sequences=5
서로 다른 hypothesis가 실제 반환되는지 확인
sequences_scores 존재 확인
beam_indices 존재 확인
compute_transition_scores 작동 확인
```

만약 HF generation score가 불안정하거나 해석이 애매하면, 반환된 N개 sequence를 teacher forcing으로 다시 점수화하는 fallback을 둔다.

---

## 14. CTranslate2 적용

### 14.1 기본 N-best 추출

CTranslate2 Whisper `generate`는 다음 설정을 사용할 수 있다.

```python
results = whisper.generate(
    features,
    prompts=[prompt_token_ids],
    beam_size=20,
    num_hypotheses=20,
    patience=1.0,
    length_penalty=1.0,
    return_scores=True,
    return_logits_vocab=False,
)

result = results[0]

for token_ids, score in zip(result.sequences_ids, result.scores):
    text = tokenizer.decode(token_ids, skip_special_tokens=True)
    print(text, score)
```

일반적으로:

```text
num_hypotheses <= beam_size
```

로 둔다.

### 14.2 score 주의점

CTranslate2 sequence score는 length penalty가 적용될 수 있다.

```text
normalized_score = cumulative_score / length^length_penalty
```

따라서 WFST 비용과 결합할 때 scale이 다를 수 있다.

대응:

```text
방법 1: normalized score를 사용하고 λ 튜닝
방법 2: length_penalty=0으로 raw cumulative score에 가깝게 사용
방법 3: CT2를 수정해 raw_cumulative_logprob과 selected_token_logprobs를 노출
```

1차 구현은 방법 1이 가장 쉽다.

### 14.3 return_logits_vocab는 1차 구현에서 불필요

N-best 합성에는 full vocab logits가 필요 없다.

필요한 것은:

```text
완성 sequence
sequence score
```

이다.

따라서:

```text
return_scores=True
return_logits_vocab=False
```

로 시작한다.

Faster-whisper는 CT2 wrapper이므로, 운영 단계에서는 wrapper가 `num_hypotheses`, `scores`, `sequences_ids`를 잘 노출하도록 맞추면 된다.

---

## 15. 과교정 방지

WFST도 오인식 사전처럼 잘못 교체될 수 있다. 과교정 방지는 필수다.

### 15.1 위험 rule

다음은 위험하다.

```text
보험금 → 보험료
고객 → 계약
상해 → 상회
```

둘 다 실제 도메인에서 가능한 단어이기 때문이다.

안전한 rule 예:

```text
손해보혐 → 손해보험
납임 → 납입
알릴 의모 → 알릴 의무
청약철애 → 청약철회
간편심싸 → 간편심사
```

### 15.2 margin

교정 후보가 원본보다 충분히 좋아야 적용한다.

```text
best_corrected_cost + margin < best_uncorrected_cost
```

차이가 작으면 원문을 유지한다.

### 15.3 보호 span

교정 전 다음 값을 placeholder로 보호한다.

```text
이름
전화번호
주민번호
계좌번호
카드번호
증권번호
금액
날짜
URL
영문 코드
```

### 15.4 로그

모든 교정에는 trace를 남긴다.

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

---

## 16. 평가 방법

비교할 시스템:

```text
A. Whisper top1
B. Whisper top1 + correction WFST
C. Whisper N-best only
D. Whisper N-best + correction WFST
E. 선택: N-best + WFST + teacher-force rescore
```

핵심 지표:

| 지표 | 의미 |
|---|---|
| CER/WER | 전체 전사 정확도 |
| Domain term accuracy | 보험 용어 정확도 |
| N-best oracle CER/WER | N개 중 정답에 가장 가까운 후보 성능 |
| Correction precision | 적용한 교정 중 실제로 맞은 비율 |
| Correction recall | 교정 가능 오류 중 실제로 고친 비율 |
| Overcorrection rate | 맞던 텍스트를 틀리게 바꾼 비율 |
| Rule coverage | rule이 커버한 오류 비율 |
| Decode latency | Whisper N-best 비용 |
| FST latency | 그래프 생성/합성 비용 |

특히 `N-best oracle CER/WER`가 중요하다.

```text
top1은 틀렸지만 N-best 안에는 정답이 자주 있다
```

이면 N-best+WFST 효과가 클 수 있다.

---

## 17. Codex용 프로젝트 구조

```text
whisper_wfst/
├── pyproject.toml
├── configs/
│   ├── hf.yaml
│   ├── ct2.yaml
│   └── correction.yaml
├── data/
│   └── correction_rules.csv
├── src/
│   └── whisper_wfst/
│       ├── types.py
│       ├── normalize.py
│       ├── hf_extractor.py
│       ├── ct2_extractor.py
│       ├── artifact_io.py
│       ├── nbest_acceptor.py
│       ├── correction_wfst.py
│       ├── compose.py
│       ├── trace.py
│       ├── rescore_hf.py
│       └── evaluate.py
└── tests/
    ├── test_nbest_acceptor.py
    ├── test_correction_wfst.py
    ├── test_composition.py
    ├── test_overlapping_rules.py
    ├── test_unicode.py
    ├── test_hf_extractor.py
    └── test_ct2_extractor.py
```

핵심 인터페이스:

```python
class HypothesisExtractor(Protocol):
    def extract(
        self,
        audio: AudioInput,
        beam_size: int,
        num_hypotheses: int,
    ) -> list[Hypothesis]:
        ...


class CorrectionEngine(Protocol):
    def correct(
        self,
        hypotheses: list[Hypothesis],
    ) -> CorrectionResult:
        ...
```

---

## 18. 필수 unit test

```text
1. 손해보혐 → 손해보험

2. 고객님 손해보혐 가입에...
   → 문장 나머지는 그대로 유지

3. 혐오 표현입니다
   → 험오 로 바뀌면 안 됨

4. 보혐 → 보험
   손해보혐 → 손해보험
   → 긴 규칙이 우선

5. 손해 보혐 / 손해보 혐
   → 등록한 변형만 처리

6. 입력·출력 길이가 다른 규칙
   → epsilon 처리

7. 동일 corrected output을 만드는 N-best 여러 개
   → 가장 낮은 total cost 선택

8. 아무 규칙도 적용되지 않음
   → ASR best hypothesis 그대로 출력

9. composition 결과 경로 없음
   → top1 fallback

10. NFC/NFD가 다른 한글
    → 정규화 후 동일하게 처리
```

가장 중요한 invariant:

```text
규칙이 적용되지 않으면
N-best+WFST 출력은 가장 낮은 ASR cost의 hypothesis와 같아야 한다.
```

---

## 19. 권장 구현 순서

### 1단계

```text
HF Whisper
beam_size=10
num_return_sequences=10
→ N-best text + score JSONL 저장
```

### 2단계

```text
교정 pair 10개
→ obligatory phrase WFST
→ N-best acceptor와 compose
```

### 3단계

```text
optional keep/correct branch
correction cost
margin
rule trace
```

### 4단계

```text
CTranslate2 adapter
beam_size=10~20
num_hypotheses=10~20
return_scores=True
```

### 5단계

```text
CER/WER
도메인 용어 정확도
과교정률
N-best oracle
속도 측정
```

### 6단계

```text
필요 시 HF teacher-force rescore
```

### 7단계

```text
더 풍부한 탐색이 필요할 때만 beam DAG 저장
```

---

## 20. 최종 Codex 작업 지시 요약

```text
Whisper에서 완성된 N-best hypothesis와 각 hypothesis의 sequence score를 추출한다.

각 hypothesis를 Unicode NFC 한글 음절 문자열로 디코딩하고,
문자열 경로의 final weight에 ASR negative log score를 부여하여 weighted acceptor를 만든다.

오인식→정인식 phrase pair로 correction WFST를 만든다.
일반 identity는 cost 0이며,
rule match 시 obligatory 또는 weighted keep/correct branch를 사용한다.

Weighted N-best acceptor와 correction WFST를 compose하고,
shortest path를 구해 최종 corrected text를 출력한다.

모든 rule application, ASR cost, correction cost, source hypothesis rank를 기록한다.
```

최종 아키텍처:

```text
Whisper N-best probability graph A_x
        ∘
Correction WFST C
        ↓
Shortest path
        ↓
Corrected transcript
```

---

## 21. 참고 링크

- OpenAI Whisper 소개: https://openai.com/index/whisper/
- Hugging Face Whisper 문서: https://huggingface.co/docs/transformers/model_doc/whisper
- Hugging Face generation utilities: https://huggingface.co/docs/transformers/internal/generation_utils
- Hugging Face `compute_transition_scores`: https://huggingface.co/docs/transformers/main_classes/text_generation
- CTranslate2 Whisper API: https://opennmt.net/CTranslate2/python/ctranslate2.models.Whisper.html
- CTranslate2 WhisperGenerationResult: https://opennmt.net/CTranslate2/python/ctranslate2.models.WhisperGenerationResult.html
- OpenFst quick tour: https://www.openfst.org/twiki/bin/view/FST/FstQuickTour
- OpenFst operations index: https://www.openfst.org/twiki/bin/view/FST/WebIndex
- Pynini PyPI: https://pypi.org/project/pynini/
