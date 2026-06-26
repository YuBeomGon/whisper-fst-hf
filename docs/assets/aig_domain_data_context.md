# AIG 보험 STT 도메인 / 데이터 컨텍스트

최종 갱신: 2026-06-26

## 1. 목적

이 문서는 Whisper WFST correction 프로젝트에서 참고할 AIG 보험 통화 STT 도메인, 데이터셋,
평가셋, 기존 실험 결과를 요약한다.

이 파일은 주변 프로젝트를 읽고 정리한 reference asset이다. 실제 구현 계약은 이후 `docs/ops/**`
또는 별도 spec에서 필요한 부분만 승격한다.

민감 통화 원문은 포함하지 않는다. 원본 데이터와 장문 transcript는 로컬 경로에서만 확인한다.

## 2. 주변 프로젝트

확인한 주요 sibling project:

| Project | 역할 |
| --- | --- |
| `../text-tune` | AIG HF dataset 설명, text-only domain adaptation 실험 |
| `../lm_fusion` | KenLM / BPE LM fusion 관점 데이터 설명과 domain term list |
| `../phrase-bias-eval` | phrase bias 실험, 도메인 용어 recall/precision 분석 |
| `../evaluating-cer` | CER 평가 규칙, normalization, dictionary registry |
| `../stt-wrapper` | generic CT2 STT wrapper 책임 경계 |
| `../stt-wrapper-sweep` | 운영 평가셋, judge CER, decode parameter sweep |
| `/data/MyProject/stt/data-gen/aig-audio-3` | AIG raw wav/label -> aligned segment -> HF dataset 생성 파이프라인 |

## 3. 도메인 요약

도메인은 한국어 AIG 보험 텔레마케팅 통화 STT다.

주요 발화 유형:

- 보험상품 안내
- 보장 설명
- 약관 및 개인정보 동의
- 해피콜
- 상담 스크립트성 고속 낭독
- 고객 응답 및 상담원 follow-up

주요 용어군:

| 범주 | 예 |
| --- | --- |
| 보험/계약 | 보험계약, 보험료, 보험금, 해약환급금, 청약철회, 보장개시일 |
| 상품/운영 | AIG 손해보험, 상품설명서, 비교안내서, 해피콜, 알림톡 |
| 의료/보장 | 급여상해수술비, 후유장해, 치주질환, 입원일당, 간호간병 통합서비스 |
| 개인정보/동의 | 개인신용정보, 고유식별정보, 동의 녹음 |
| 숫자/금액/단위 | 원, %, 전화번호, 주민번호 앞자리, 금액 콤마 |

도메인 특성:

- 숫자, 금액, 단위가 자주 나온다.
- 보험/의료 복합명사가 길고 드물게 나온다.
- 스크립트 낭독 구간은 빠르고 단조로워 compression/gating 계열 파라미터에 민감하다.
- 상담원 채널 `_l`과 고객 채널 `_r`의 난도와 성격이 다르다.

## 4. HF Chunk Dataset

정본 설명 문서:

- `../text-tune/docs/dataset_description.md`

실제 경로:

```text
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset
```

형식:

```python
from datasets import load_from_disk
ds = load_from_disk("/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset")
# DatasetDict({ train, validation })
```

규모:

| Split | Rows | Audio time | Chunk strategy | Source wav 수 |
| --- | ---: | ---: | --- | ---: |
| `train` | 2,556 | 약 9.70h | `duration_aware_overlap` | 24 |
| `validation` | 424 | 약 1.51h | `deterministic_non_overlap` | 10 |
| total | 2,980 | 약 11.2h | mixed | 34 |

확정 운용:

- 기존 `train`은 train으로 사용한다.
- 기존 `validation`은 test로 사용한다.
- 별도 valid split은 없다.
- train과 validation 사이 `source_wav` 중복은 0건으로 보고되어 있다.

핵심 schema:

| Column | 의미 |
| --- | --- |
| `audio` | raw float waveform list. HF `Audio` feature가 아니다 |
| `sampling_rate` | 항상 16000 |
| `text` | 정답 transcript |
| `split` | `train` 또는 `validation` |
| `chunk_id` | chunk id |
| `source_wav` | 원본 wav 상대경로 |
| `source_start`, `source_end` | 원본 wav 내 시간 |
| `cut_start`, `cut_end`, `cut_duration` | 실제 잘린 구간 |
| `source_segment_ids` | 원본 label segment id 목록 |
| `segment_ranges` | segment별 시간 범위 |
| `chunk_strategy` | chunk 생성 전략 |
| `variant_id`, `run_id` | 생성 provenance |

구현 주의:

- `audio`는 `np.array(row["audio"], dtype=np.float32)`로 변환해야 한다.
- sampling rate는 16000이다.
- train chunk는 모두 30초 이하로 보고됐다.
- validation에는 30초 초과 chunk 2건이 있으며, Whisper 30초 window 기준으로 분할 또는 제외가 필요하다.

## 5. Alignment / Data Generation Pipeline

정본 문서:

- `/data/MyProject/stt/data-gen/aig-audio-3/docs/SSOT.md`
- `/data/MyProject/stt/data-gen/aig-audio-3/README.md`

Canonical inputs:

```text
data/raw/label/**/*.txt
data/normalized/label/**/*.jsonl
data/raw/wav/**/*.wav
```

주요 output:

```text
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/aligned_segments.jsonl
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/aligned_segments_unaligned.jsonl
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/aligned_segments_summary.json
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/alignment_coverage_summary.json
/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset
```

`aligned_segments.jsonl`은 WFST rule 후보 추출에 특히 중요하다. 각 record에는 label text와
Whisper transcript evidence가 함께 있다.

중요 필드:

| Field | 의미 |
| --- | --- |
| `id` | aligned segment id |
| `source_wav` | 원본 wav |
| `source_label` | 원본 label |
| `label_segment_id` | label segment |
| `start`, `end` | wav 내 aligned 시간 |
| `text` | clean label text |
| `whisper_text` | alignment용 Whisper transcript |
| `alignment_score`, `coverage` | alignment 품질 |
| `reason` | verify/review/failure reason |
| `verify_cer`, `verify_coverage`, `verify_whisper_text` | verify-cut 진단 값 |

alignment coverage summary:

```json
{
  "source_file_count": 34,
  "total_audio_duration": 41427.13875,
  "aligned_audio_duration": 31051.142,
  "uncovered_audio_duration": 10375.99675,
  "audio_coverage_ratio": 0.749536,
  "aligned_segment_count": 3874,
  "unaligned_segment_count": 30,
  "label_segment_count": 3904,
  "label_coverage_ratio": 0.992316
}
```

활용:

- `text` vs `whisper_text` diff에서 실제 hyp -> ref correction 후보를 추출한다.
- `alignment_score`, `coverage`, `verify_cer`를 rule 후보 신뢰도 필터로 쓴다.
- 긴 스크립트 span은 바로 rule로 쓰지 않고 별도 검토한다.

## 6. 운영 평가셋

정본 문서:

- `../stt-wrapper-sweep/docs/ops/eval-contract.md`

운영 평가셋은 상담사 채널 `_l`의 judge eval-of-record를 기준으로 한다.

| Date | Scored files |
| --- | ---: |
| `20250704` | 11 |
| `20250715` | 11 |
| `20250813` | 13 |
| total | 35 |

평가 wav 위치:

```text
/data/MyProject/stt/aig/stt-engine/shared/debug/input/AIG_녹취반출_20250704
/data/MyProject/stt/aig/stt-engine/shared/debug/input/AIG_녹취반출_20250715
/data/MyProject/stt/aig/stt-engine/shared/debug/input/AIG_녹취반출_20250813
```

primary metric:

```text
cer_micro = sum(edits) / sum(ref_chars)
```

운영 backend:

```bash
CER_BACKEND=judge
```

judge normalization:

- NFC
- `[INAUDIBLE]` 제거
- 문장부호 제거
- 소문자화
- 모든 공백 제거

주의:

- `CER_BACKEND=jiwer` 결과를 운영 best로 쓰지 않는다.
- partial eval 결과를 운영 record에 섞지 않는다.
- 날짜 subset 또는 파일 subset을 best 비교에 쓰지 않는다.

WFST 프로젝트에서 이 평가셋은 최종 offline MVP 평가나 regression 확인에 사용할 수 있다.

## 7. CER / Normalization 규칙

정본 문서:

- `../evaluating-cer/docs/02_domain_rules.md`
- `../evaluating-cer/docs/03_current_system_map.md`

주요 입력 규칙:

- ref는 평가 기준 텍스트다.
- hyp는 모델 출력 텍스트이며 주 입력 형식은 `.srt`다.
- cue 번호, 타임코드, `[window seek=...]` 메타는 비교 대상이 아니다.
- 채널은 filename suffix로 본다. `_l`은 상담원, `_r`은 고객, 그 외는 unknown이다.
- 같은 stem이 중복되거나 unmatched인 경우 정책적으로 exclude/error를 선택한다.

전사 규칙:

- 채널별 독립 전사다.
- 반대 채널 문맥으로 빈 구간을 추정하지 않는다.
- reference는 기존 STT 결과를 보고 교정하는 방식이 아니라 from-scratch 전사다.
- 확정이 안 되면 추측하지 않고 `[INAUDIBLE]`를 넣는다.
- 개인정보는 `<원문> [TAG]` 형식으로 비식별화한다.
- 정형 문구의 빠른 낭독은 `[SCRIPT_START] ... [SCRIPT_END]`로 감싼다.

정규화 사전 종류:

| Dict | 역할 |
| --- | --- |
| `filler.txt` | 간투어 또는 무시 대상 token |
| `equiv_map.tsv` | 동치 표현 |
| `confusion.json` | hyp-only 오인식 교정 |
| `english_pairs.tsv` | 영문 약어 / 한글 대응 |
| `unit_pairs.tsv` | 단위 기호 / 한글 대응 |

중요한 차이:

- CER normalization은 scoring 목적이다.
- WFST correction normalization은 원문 보존과 trace가 중요하다.
- 따라서 CER normalization을 그대로 correction 전처리로 쓰면 안 된다.

## 8. Dictionary Registry

경로:

```text
../evaluating-cer/storage/dictionary_registry.json
```

확인 결과:

- entries: 51
- status: 모두 `applied`
- op: 모두 `SUB`
- direction: `hyp_to_ref`

상위 support 예:

| Support | Hyp | Ref | Note |
| ---: | --- | --- | --- |
| 62 | 후유장애 | 후유장해 | term |
| 17 | 만기일의다음날부터갱신 | 만기일다음날부터갱신 | span |
| 13 | 모바일과우편이메일문자알림톡으로받아 | 모바일과우편문자알림톡으로받아 | span |
| 13 | ard | aig | review_safe |
| 10 | o건입니다 | 0건입니다 | review_safe |
| 9 | 급여상의 | 급여상해 | review_safe |
| 7 | 통합상의 | 통합상해 | review_safe |
| 7 | 염자 | 염좌 | review_safe |
| 7 | 하나여 | 한하여 | review_safe |
| 6 | o건 | 0건 | review_safe |
| 6 | 라인화 | 라이나 | review_safe |

WFST seed로 쓰기 좋은 후보:

- `후유장애 -> 후유장해`
- `급여상의 -> 급여상해`
- `통합상의 -> 통합상해`
- `염자 -> 염좌`
- `라인화 -> 라이나`
- `o건 -> 0건`
- `o건입니다 -> 0건입니다`

주의:

- registry에는 긴 script span correction도 섞여 있다.
- 긴 span은 자유대화 overcorrection 위험이 있으므로 바로 rule로 승격하지 않는다.
- support, sample count, rule length, domain term 여부, free-talk risk를 기준으로 필터링해야 한다.

## 9. Phrase Bias 실험과 교훈

정본 문서:

- `../phrase-bias-eval/docs/experiments.md`
- `../phrase-bias-eval/experiments/phrase_bias.json`

평가 조건:

- 데이터: 상담원 채널 `_l` 5개, 21~29분
- 도메인 용어: 171개
- base model: `deepdml/faster-whisper-large-v3-turbo-ct2`
- finetune model: `v1_t0023_ct2_float16`

핵심 결과:

| 구성 | CER | Domain recall | Precision | Latency avg |
| --- | ---: | ---: | ---: | ---: |
| base turbo, bias off | 0.1908 | 0.554 | 0.948 | 59.2s |
| AIG finetune, bias off | 0.108 | 0.792 | 0.956 | 56.3s |
| base turbo, phrase bias exp2 | 0.1868 | 0.552 | 0.960 | 59.2s |

교훈:

- finetune이 가장 강했다.
- phrase bias는 제한적이고 불안정하다.
- 짧고 흔한 부분어를 넓게 bias하면 과발화와 오인식이 늘 수 있다.
- 효과는 길고 드물고 baseline이 놓치는 전문어에 집중된다.
- 모델이 일관되게 다른 표면형으로 뱉는 것은 bias보다 후처리/WFST correction 대상이다.

분류:

| Category | 모델 출력 양상 | 적절한 도구 | 예 |
| --- | --- | --- | --- |
| A | 첫 token은 맞고 뒤를 흘림 | phrase bias | 약침치료, 입원일당, 비교안내서 |
| B | 일관된 다른 표면형으로 출력 | deterministic post-process / WFST | 후유장애 -> 후유장해, 청약 철회 -> 청약철회 |
| C | 전혀 안 뱉음 | finetune / stronger model / prompt | 첩약처방, 영구치, 치주질환 |

WFST 프로젝트의 1차 대상은 Category B다.

## 10. Text-Only Domain Adaptation 실험과 교훈

정본 문서:

- `../text-tune/docs/experiments/CONCLUSIONS.md`

결론:

- text-only로 학습한 cross-attention bias 주입 방식은 이 데이터/구성에서 baseline을 개선하지 못했다.
- oracle text를 학습해도 개선이 없어서 단일 글로벌 text bias 구조 자체의 한계가 확인됐다.
- 후속 후보로는 shallow fusion, train/infer 조건 일치, LoRA 등이 남았지만, WFST correction과 직접 겹치는 영역은 아니다.

WFST 관점 교훈:

- 전역 domain prior를 강하게 넣는 방식은 환각 또는 overcorrection 위험이 있다.
- evidence 기반 hyp -> ref surface correction이 더 좁고 안전한 접근이다.

## 11. Wrapper / Runtime 경계

정본 문서:

- `../stt-wrapper/docs/SSOT.md`
- `../stt-wrapper/docs/design.md`

핵심 원칙:

- wrapper는 generic STT wrapper다.
- wrapper는 domain glossary, replacement rule, corpus, evaluation policy를 소유하지 않는다.
- caller/pipeline이 file I/O, resampling, channel handling, VAD, diarization, domain corpus, post-correction, evaluation report를 소유한다.

입력 경계:

```python
audio: np.ndarray  # mono float waveform, preferably float32
sr: int            # preferably 16000
```

WFST 프로젝트도 이 경계를 따른다. 즉, WFST correction은 wrapper 내부가 아니라 pipeline/caller 레이어에서
N-best artifact를 받아 수행하는 것이 맞다.

## 12. WFST Correction을 위한 데이터 활용 방향

### 12.1 Rule seed 후보 생성

우선순위:

1. `dictionary_registry.json`의 `applied`, `hyp_to_ref`, support 높은 term/review_safe 항목
2. `aligned_segments.jsonl`의 `text` vs `whisper_text` diff에서 반복 관측되는 표면형 오류
3. phrase-bias 실험에서 Category B로 분류된 표면형 오류

초기 rule 후보 예:

```text
후유장애 -> 후유장해
급여상의 -> 급여상해
통합상의 -> 통합상해
염자 -> 염좌
라인화 -> 라이나
o건 -> 0건
o건입니다 -> 0건입니다
청약 철회 -> 청약철회
알릴 의모 -> 알릴 의무
```

각 후보는 다음 metadata를 가져야 한다.

- source path
- support count
- sample count
- affected files
- category: term / review_safe / span
- free-talk risk
- suggested mode: obligatory / optional
- suggested priority

### 12.2 Rule 승격 기준

MVP에서 바로 승격 가능한 rule:

- 짧은 일반어가 아니다.
- ref/hyp가 모두 실제 관측 evidence를 가진다.
- support가 복수 file 또는 복수 sample에서 확인된다.
- 개인정보나 금액을 직접 바꾸지 않는다.
- 자유대화에서 정상 표현일 가능성이 낮다.
- correction 후 domain term 또는 표준 표면형이 된다.

보류해야 하는 rule:

- 긴 script span 전체 교정
- 문체 차이만 교정하는 rule
- `고객 -> 계약`처럼 둘 다 정상 단어인 rule
- 짧고 흔한 부분어
- 숫자/금액을 추정으로 바꾸는 rule

### 12.3 Evaluation manifest에 필요한 필드

WFST evaluation manifest는 최소한 다음을 가져야 한다.

- `segment_id`
- `audio_ref`
- `channel`
- `split`
- `ref_text`
- `hyp_text` 또는 N-best artifact ref
- `is_free_talk`
- `is_script_span`
- `domain_terms`
- `allowed_rules`
- `source_wav`
- `source_start`
- `source_end`

## 13. 핵심 결론

이 프로젝트의 WFST correction은 일반적인 보험 용어 사전 주입이 아니라, 실제 AIG 통화에서 반복 관측된
`hyp -> ref` 표면형 오류를 evidence 기반으로 교정하는 시스템이어야 한다.

가장 먼저 가져갈 자산:

1. `dictionary_registry.json`의 applied hyp_to_ref entries
2. `aligned_segments.jsonl`의 label/whisper_text pairs
3. `phrase_bias.json`의 도메인 용어 목록
4. `stt-wrapper-sweep`의 judge evaluation contract
5. `evaluating-cer`의 normalization과 PII/script/inaudible 규칙

이 다섯 가지를 연결하면 correction rule seed, N-best oracle 평가, free-talk overcorrection 평가를
초기 phase에서 재현 가능하게 만들 수 있다.

