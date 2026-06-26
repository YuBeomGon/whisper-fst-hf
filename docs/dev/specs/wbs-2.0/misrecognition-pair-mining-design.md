# Misrecognition Pair Mining Design

Date: 2026-06-26

Branch: `docs/misrecognition-pair-mining-design`

## 1. Purpose

이 문서는 보험 상담 도메인 오인식을 줄이기 위한 `wrong -> right` pair 후보 수집 설계를 정의한다.

현재 v1 PoC는 synthetic/mock artifact 기준으로 끝났으므로, WBS 2.0 전에 실제 label/SRT 기반 pair mining
전략을 먼저 고정한다. 목표는 모든 `_l` SRT run을 evidence source로 사용하되, noisy pair를 직접 rule로
승격하지 않고 review 가능한 후보 사전으로 만드는 것이다.

## 2. Inputs

### 2.1 Human Labels

대상 경로:

```text
/data/MyProject/stt/aig/stt-engine/shared/annotations/*/*_l.txt
```

현재 확인된 `_l.txt` label은 47개다.

| Batch | Count |
| --- | ---: |
| `AIG_녹취반출_20250704` | 14 |
| `AIG_녹취반출_20250715` | 17 |
| `AIG_녹취반출_20250813` | 16 |

같은 base name의 `_l.docx`도 2개 있으나, 현재 pair mining 입력은 `_l.txt`를 우선한다.

### 2.2 SRT Runs

대상 경로:

```text
/data/MyProject/stt/aig/stt-engine/shared/debug/output/**/*_l.srt
```

나중에 실제 pair 후보를 만들 때는 모든 run을 훑는다. 단, 조사 단계와 WBS 작성 단계에서는 전체 SRT
본문을 읽지 않고 run inventory와 소수 sample만 확인한다.

SRT는 ASR hypothesis source다. 같은 음성이 여러 sweep/run에 반복 포함되므로 support count는 반드시
run 기준과 source file 기준을 분리한다.

## 3. Observed Label Formats

현재 label은 대부분 다음 구조다.

```text
1
...

2
...
```

숫자 index는 대략 30초 block을 의미하지만 실제 시간과 오차가 있을 수 있다.

확인된 형식 변형:

| Type | Count | Policy |
| --- | ---: | --- |
| 숫자 block이 첫 줄부터 연속 | 43 | normal parser |
| index가 첫 줄이 아님 | 2 | header/body 분리 후 parser |
| index가 없음 | 1 | whole-file 또는 paragraph fallback, low confidence |
| 숫자-only 본문이 index처럼 보일 수 있음 | 1 | expected sequence와 block boundary로 검증 |
| 매우 짧음 | 1 | pair mining 제외 후보 |

확인된 square tag:

```text
[INAUDIBLE]
[SCRIPT_START]
[SCRIPT_END]
[NAME]
[CONTACT]
[ADDR]
[GOODS]
[PAY]
[AI_START]
[AI_END]
```

`[SCRIPT_START]`와 `[SCRIPT_END]`는 일부 파일에서 개수가 맞지 않는다. script span은 strict stack으로
처리하지 않고 tolerant range marker로 다룬다.

## 4. Label Normalization

### 4.1 Output Views

label parser는 같은 입력에서 세 가지 view를 만든다.

| View | Purpose |
| --- | --- |
| `raw_text` | 원문 재현과 audit |
| `normalized_ref_text` | SRT와 비교할 reference |
| `protected_mask` | pair 추출 금지 span |

repository에는 민감 원문을 commit하지 않는다. commit 대상은 parser logic, synthetic fixture, 집계 report,
checksum, candidate schema다.

### 4.2 Short Label Exclusion

너무 짧은 label은 pair mining에서 제외한다.

초기 default:

```text
exclude if index_count <= 2
exclude if normalized_ref_text length < 120 chars
```

제외된 파일은 버리지 않고 exclusion manifest에 이유만 남긴다.

### 4.3 Square Tags

비교용 text에서는 square tag를 버린다.

```text
[INAUDIBLE]    -> remove
[SCRIPT_START] -> remove
[SCRIPT_END]   -> remove
[NAME]         -> remove
[CONTACT]      -> remove
[ADDR]         -> remove
[GOODS]        -> remove
[PAY]          -> remove
[AI_START]     -> remove
[AI_END]       -> remove
```

단, `[NAME]`, `[CONTACT]`, `[ADDR]` 주변 phrase는 protected span으로 표시하고 pair 후보로 추출하지 않는다.
tag text 자체는 candidate CSV에 넣지 않는다.

### 4.4 Angle Markup

`<...>` 계열 markup은 source마다 의미가 섞일 수 있으므로 보수적으로 처리한다.

정책:

1. `<...> [NAME]`, `<...> [CONTACT]`, `<...> [ADDR]` 형태는 전체 span을 제거하고 protected 처리한다.
2. 명시적인 correction pair 형태는 오른쪽을 정인식으로 사용한다.
   - 예: `<wrong>/<right>`, `<wrong> / <right>`, `<wrong>-><right>`, `<wrong> => <right>`
3. correction pair로 판정되지 않는 standalone `<...>`는 비교용 text에서 제거한다.
4. standalone angle 내용이 도메인 term일 수 있는지는 별도 audit에서 sample review한다. 자동으로 rule source로
   쓰지 않는다.

이 정책은 사용자가 말한 "`<>/<>` 같은 경우 오른쪽이 정인식일 가능성이 높다"는 가정을 반영하되, 개인정보와
도메인 term markup이 섞이는 리스크를 피하기 위한 것이다.

### 4.5 Index Block Parsing

normal parser:

```text
index line: ^\d{1,4}$
block_start_sec = (index - 1) * 30
block_end_sec = index * 30
```

시간 오차를 고려해 alignment에는 tolerance를 둔다.

```text
default_label_window_tolerance_sec = 5
```

예외 처리:

- index가 첫 줄이 아니면 첫 valid sequence 전까지 header로 분리한다.
- index가 non-monotonic이면 candidate index sequence를 재탐색한다.
- index가 없으면 whole-file fallback으로 처리하고 confidence를 낮춘다.
- 숫자-only line이 본문일 수 있으므로 연속 index sequence에 맞지 않으면 text로 취급한다.

## 5. SRT Normalization

SRT parser는 다음 필드를 생성한다.

```text
run_id
run_path
source_stem
channel
srt_index
start_sec
end_sec
raw_text
normalized_hyp_text
```

정규화:

- Unicode NFC
- SRT index/timestamp 제거
- square/angle tag 제거
- repeated whitespace collapse
- punctuation normalization은 scoring view에서만 사용

SRT run metadata는 path에서 추출한다.

```text
debug/output/<run_name>/<variant>/<file>_l.srt
```

## 6. Alignment Strategy

### 6.1 Rough Time Alignment

label index block과 SRT timestamp를 먼저 rough align한다.

```text
label block n ~= [(n - 1) * 30, n * 30]
SRT block belongs to label block if midpoint overlaps tolerant window
```

time 기반 매칭이 가능한 경우만 high confidence로 둔다.

### 6.2 Text Sequence Alignment

rough window 안에서 `normalized_ref_text`와 `normalized_hyp_text`를 sequence align한다.

초기 구현은 standard library 기반으로 시작한다.

- block 단위: `difflib.SequenceMatcher`
- phrase 후보: char diff를 eojeol boundary로 확장
- 이후 필요하면 RapidFuzz 같은 dependency를 별도 phase에서 검토

alignment confidence는 다음 신호로 계산한다.

```text
time_overlap_ratio
normalized_text_similarity
diff_span_length
protected_span_overlap
```

low confidence segment는 pair 후보를 만들지 않거나 `needs_review`로만 둔다.

## 7. Pair Extraction

diff span에서 후보를 만든다.

```text
wrong = SRT hyp phrase
right = label ref phrase
```

초기 filter:

```text
min_hangul_chars = 2
max_chars = 40
max_eojeol = 8
reject if wrong == right after normalization
reject if pair touches protected span
reject if either side is digit-only
reject if right is empty
reject if wrong is empty unless insertion rule is explicitly enabled later
```

phrase boundary:

- diff span을 좌우 eojeol boundary로 확장한다.
- 너무 긴 span은 sentence-level mismatch로 보고 pair 후보에서 제외한다.
- 조사/어미 차이만 있는 pair는 low priority로 둔다.

## 8. Support Counting

모든 SRT run을 사용하되 support 의미를 분리한다.

| Field | Meaning |
| --- | --- |
| `support_run_count` | 몇 개 run에서 관측됐는가 |
| `support_file_count` | 몇 개 distinct source file에서 관측됐는가 |
| `support_batch_count` | 몇 개 batch에서 관측됐는가 |
| `support_variant_count` | 몇 개 run variant에서 관측됐는가 |

최종 rule 승격은 `support_run_count`가 아니라 `support_file_count`, `support_batch_count`, review 결과를
우선한다. 같은 파일을 100개 sweep에서 반복한 것은 "100개 독립 관측"이 아니다.

## 9. Candidate Classification

candidate는 자동으로 rule이 되지 않는다.

| Class | Meaning |
| --- | --- |
| `candidate` | 자동 추출 후보 |
| `needs_review` | confidence 낮거나 위험 신호 있음 |
| `obligatory` | 사람이 검토해 항상 교정해도 된다고 승인 |
| `optional` | context/margin/gating 필요 |
| `reject` | rule 금지 |

초기 자동 risk flag:

- `protected_overlap`
- `short_label_source`
- `low_alignment_confidence`
- `angle_markup_source`
- `script_span_unbalanced`
- `both_sides_domain_valid`
- `free_talk_risk`
- `single_file_only`
- `test_source_only`

## 10. Leakage Policy

pair mining source와 final evaluation source를 분리한다.

원칙:

- 모든 SRT run에서 candidate를 만들 수는 있다.
- 하지만 final eval에만 존재하는 pair를 seed rule로 승격하면 leakage다.
- 파일 단위 split을 먼저 고정한다.
- rule seed는 `rule_mining` 또는 `dev_review` source에서만 만든다.
- `eval_holdout` source에서 나온 pair는 report에는 남기되 rule로 쓰지 않는다.

WBS 2.0에서 split manifest를 별도 phase 산출물로 만든다.

## 11. Outputs

대용량 원문 artifact는 repository에 넣지 않는다.

committed outputs:

```text
docs/reports/audits/label_format_audit.md
docs/reports/audits/srt_run_inventory.md
data/pair_candidates.sample.csv
data/pair_review_schema.csv
```

ignored/local outputs:

```text
outputs/pair_mining/pair_candidates.csv
outputs/pair_mining/pair_candidates.jsonl
outputs/pair_mining/pair_source_manifest.json
outputs/pair_mining/alignment_debug/
```

candidate CSV schema:

```text
pair_id
wrong
right
normalized_wrong
normalized_right
support_run_count
support_file_count
support_batch_count
source_files
source_runs
first_source_label
first_source_srt
channel
time_windows
alignment_confidence
risk_flags
suggested_class
review_class
review_note
```

## 12. WBS 2.0 Implications

WBS 2.0은 이 설계를 기준으로 다음 phase를 둔다.

```text
P14. Real Label Format Audit / Parser v2
P15. SRT Run Inventory and Matching
P16. Misrecognition Pair Mining
P17. Pair Review / Rule Source Audit v2
P18. Real HF Dataset / Runtime Smoke
P19. Real HF N-best Targetability
P20. Leakage-safe Correction Eval
P21. Calibration Sweep
P22. PoC v2 Go / No-Go
```

WBS 2.0 작성 전에는 이 문서를 먼저 review한다.

## 13. Acceptance Criteria

- label parser가 47개 `_l.txt` 형식 변형을 분류할 수 있다.
- 너무 짧은 label과 index 없는 label을 명시적으로 처리한다.
- square tag는 비교 text에서 제거된다.
- angle correction markup은 오른쪽 정인식만 보존하되, 개인정보/protected span은 제거된다.
- 모든 `_l.srt` run을 inventory할 수 있다.
- pair support는 run/file/batch 기준으로 분리된다.
- candidate가 자동으로 rule로 승격되지 않는다.
- leakage-safe split과 review gate가 WBS 2.0에 반영된다.
