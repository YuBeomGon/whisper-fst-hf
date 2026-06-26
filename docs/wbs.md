# Whisper WFST Project WBS

- version: 4
- 최종 갱신: 2026-06-26
- 현재 상태: P0/P1/P2/P3 완료, P2 결과는 현재 환경 기준 Pynini backend unavailable
- 기준 설계: `docs/dev/specs/project-design.md`
- 현재 PoC runtime: Hugging Face Transformers Whisper
- 주요 reference:
  - `docs/assets/whisper_wfst_composition_research.md`
  - `docs/assets/aig_domain_data_context.md`
  - `docs/ops/evaluation-calibration-design.md`
  - `docs/reports/audits/wfst-domain-feasibility-research.md`

## 1. 역할

이 문서는 Whisper WFST 프로젝트의 실행 척추다. 설계 본문을 길게 담기보다 phase 순서, 상태,
의존성, 크기, branch/spec/plan/report 산출물, 완료 기준을 관리한다.

현재 repository에는 P0 governance 문서, P1 Python scaffold, P2 backend feasibility, P3 core contract가 있다. 이후 구현은 이 WBS의 phase를
따라 진행한다.

`docs/assets/**`는 read-only reference다. WBS 수행 중 수정하지 않는다.

현재 PoC는 HF Transformers Whisper를 대상으로 한다. CTranslate2/faster-whisper integration은 이번
PoC 범위가 아니며, 필요성이 확인될 때 후속 WBS로 분리한다.

## 2. 운영 전제

P2 이후 각 build phase는 대화 기억이 아니라 repository 문서와 branch를 기준으로 진행한다.

```text
WBS phase 선택
-> phase branch 생성
-> phase design spec 작성/확정
-> implementation plan 작성/확정
-> implement
-> verify
-> review
-> fix
-> final completion criteria 확인
-> status/WBS/changelog update
-> integration step: merge + push only after explicit approval
```

세부 loop와 stop condition은 `docs/ops/phase-loop.md`를 따른다.

MVP phase의 기본 검증 후보:

```bash
uv run --group dev ruff check .
uv run --group dev pytest
git diff --check
```

scaffold 전에는 해당 명령이 없을 수 있다. 그 경우 phase report에 실행 불가 이유와 대체 검증을 남긴다.

범례:

- `todo`: 시작 전
- `doing`: 진행 중
- `done`: 완료
- 크기: `S`, `M`, `L`

P2 이후 phase entry는 가능한 한 아래 필드를 가진다.

- `branch`: phase 작업 branch. 예: `wbs/P2-fst-backend-feasibility`
- `spec`: phase design spec. `docs/dev/specs/**`
- `plan`: implementation plan. `docs/dev/plans/**`
- `예상 산출물`: phase 수행 중 생성/갱신될 결과물
- `ops 승격 후보`: current 운영 계약으로 승격 가능한 문서 후보. 없으면 `none`

WBS가 너무 커서 한 branch나 한 review 단위로 보기 어렵다면 구현 전에 하위 WBS로 분할한다.
branch, spec, plan, implementation, test, review, report는 같은 WBS ID로 추적 가능해야 한다.

## 3. Phases

### P0. Governance / Docs Scaffold - done S

목표: 이후 phase loop가 대화 기억이 아니라 repository 문서 기준으로 돌아가도록 최소 운영 문서를 만든다.

dep: none

예상 산출물:

- `AGENTS.md`
- `docs/index.md`
- `docs/status.md`
- `docs/CHANGELOG.md`
- `docs/ops/governance.md`
- `docs/ops/coding-conventions.md`
- `docs/ops/environment.md`
- `docs/ops/phase-loop.md`
- optional: `scripts/hooks/protect_governance_docs.sh`

범위:

- `docs/assets/**` 수정 금지 원칙 고정
- current / reference / history / evidence / review 문서 구분
- SSOT 원칙 정의
- status는 현재 WBS와 다음 액션만 담도록 정의
- current WBS SSOT는 `docs/wbs.md`로 고정하고 ops 문서는 이를 링크만 하도록 정의
- WBS ID 기반 작업 규칙 정의
- commit 전 governance protected docs 승인 규칙 정의
- code, schema, config, artifact, test 원칙 정의

비범위:

- Python package scaffold
- WFST 구현
- Whisper 실행
- correction rule 작성

완료 기준:

- 다음 세션에서 읽을 문서 순서가 `AGENTS.md`에 명시됨
- `docs/assets/**`가 read-only reference로 문서화됨
- `docs/dev/specs/project-design.md`와 `docs/wbs.md`가 index에서 연결됨
- WBS current 문서 위치가 `docs/wbs.md`로 확정됨
- governance 문서와 status 문서가 서로 모순되지 않음

### P1. Python Scaffold / Environment - done S

목표: 구현과 검증을 시작할 수 있는 최소 Python package scaffold를 만든다.

dep: P0

예상 산출물:

- `pyproject.toml`
- `uv.lock`
- `src/whisper_wfst/__init__.py`
- `tests/test_scaffold.py`
- `.gitignore`
- `configs/`
- `data/`
- `outputs/` ignored policy

범위:

- Python version 결정
- dependency group 결정: runtime, dev, optional whisper/fst extras
- pytest, ruff wiring
- package import smoke test
- large artifact ignore policy

비범위:

- Pynini/OpenFST dependency 확정
- actual WFST implementation
- Whisper model download or inference

완료 기준:

- package import smoke test가 통과함
- `ruff check`와 `pytest` 실행 경로가 문서화됨
- large local artifacts가 git에 들어가지 않도록 ignore 규칙이 있음
- `docs/ops/environment.md`가 scaffold 기준 명령을 담음

### P2. FST Backend Feasibility - done M

목표: WFST backend를 확정하기 전에 Pynini/OpenFST 설치와 최소 compose/shortest path 동작을 검증한다.

dep: P1
branch: `wbs/P2-fst-backend-feasibility`
spec: `docs/dev/specs/p2-fst-backend-feasibility.md`
plan: `docs/dev/plans/p2-fst-backend-feasibility-plan.md`
loop level: Level 1
result: 현재 uv/Python 3.12.4 환경에서 `pynini` import 실패. P3 이후 구현은 Pynini backend를
무조건 전제하지 않고 availability check와 fail-fast 또는 fallback 전제를 포함해야 한다.

예상 산출물:

- `docs/reports/probes/fst_backend_feasibility.md`
- `tests/test_fst_backend_smoke.py`
- optional config: backend selection

ops 승격 후보:

- none

범위:

- Pynini 설치 가능 여부 확인
- Unicode utf8 token type smoke
- `손해보혐 -> 손해보험` cross/compose/shortest path smoke
- synthetic N-best acceptor와 correction transducer compose smoke
- shortest path output string roundtrip
- 공백 처리 smoke
- epsilon insertion/deletion이 필요한 길이 차이 correction smoke
- 실행 Python version 기록. Pynini/OpenFST 설치 제약이 있으면 Python 3.11/3.12 기준으로 우선 확인
- dependency 설치 방식 기록
- backend unavailable 시 fail-fast 정책 정의

비범위:

- full correction rule compiler
- Whisper extractor
- evaluation harness

완료 기준:

- Pynini backend를 쓸 수 있는지 yes/no가 report에 남음
- yes이면 한글 acceptor, cross, compose, shortest path, output string roundtrip test가 통과함
- 공백과 길이 차이 correction smoke 결과가 report에 남음
- no이면 대체 전략 또는 blocker가 명시됨
- backend 결정이 P3 이후 구현 계획에 반영됨

### P3. Core Contracts / DTO / Config - done M

목표: N-best artifact, correction rule, correction result trace의 current data contract를 코드와 문서로 고정한다.

dep: P2
branch: `wbs/P3-core-contracts`
spec: `docs/dev/specs/p3-core-contracts-dto-config.md`
plan: `docs/dev/plans/p3-core-contracts-dto-config-plan.md`
loop level: Level 2
result: N-best artifact, correction rule CSV, backend status, correction trace DTO와 JSON/JSONL/CSV IO helper를
구현했다. P2의 Pynini unavailable 결과는 `configs/correction.yaml`과 `BackendStatus` contract에 반영했다.

예상 산출물:

- `docs/ops/schema.md`
- `configs/correction.yaml`
- `data/correction_rules.csv`
- `src/whisper_wfst/types.py`
- `src/whisper_wfst/artifact_io.py`
- `src/whisper_wfst/rule_io.py`
- `tests/test_artifact_io.py`
- `tests/test_rule_io.py`

ops 승격 후보:

- `docs/ops/schema.md`: P3 contract가 current 구현/evaluation 기준으로 충분하면 승격

범위:

- `Hypothesis` DTO
- N-best artifact schema
- correction rule CSV schema
- `left_context` / `right_context`는 MVP에서 reserved이며 non-empty 값은 validation error로 처리
- obligatory/optional mode validation
- correction trace schema
- enabled/priority/cost validation
- score metadata validation: `score_source`, `score_is_logprob`, `length_penalty`, `asr_cost`
- P2 결과 반영: backend availability/fail-fast 상태를 config 또는 runtime contract에서 표현
- JSON/JSONL read/write helpers

비범위:

- actual WFST composition
- Whisper runtime integration
- CER/WER evaluation

완료 기준:

- invalid rule은 조용히 통과하지 않음
- non-empty `left_context` / `right_context`가 silent ignore되지 않고 reject됨
- duplicate hypothesis dedupe 기준이 contract에 명시됨
- `asr_cost` 산출 규칙과 score provenance가 artifact contract에 명시됨
- sample N-best artifact와 sample rule CSV가 test fixture로 존재함
- schema 문서와 DTO validation이 서로 모순되지 않음

### P3.5. Rule Source Audit / Seed Rule Review - todo M

목표: correction rule seed가 어떤 데이터에서 왔는지 검증하고, final eval leakage 없이 안전한 seed만 분리한다.

dep: P3
branch: `wbs/P3.5-rule-source-audit`
spec: `docs/dev/specs/p3.5-rule-source-audit.md`
plan: `docs/dev/plans/p3.5-rule-source-audit-plan.md`
loop level: Level 1

예상 산출물:

- `docs/reports/probes/rule_source_audit.md`
- `data/correction_rules_seed.csv`
- `tests/test_rule_source_audit.py`

ops 승격 후보:

- none

범위:

- `dictionary_registry.json`, `aligned_segments.jsonl`, phrase-bias 결과의 rule source 정리
- rule_id, wrong, right, source, provenance, support, source_wav, segment_id 기록
- final eval 유래 여부 표시
- free-talk risk label
- obligatory / optional / disabled 후보 분류
- 긴 script span, number/PII, low-support rule 보류

비범위:

- automatic rule promotion
- final production rule 확정
- LLM 기반 rule 생성

완료 기준:

- seed rule마다 provenance와 support가 기록됨
- final eval 유래 rule은 final claim에 사용하지 않도록 표시됨
- `safe_only` seed CSV가 생성됨
- high-risk rule은 disabled 또는 optional 후보로만 남음

### P4. Normalization / Protection Layer - todo M

목표: 한국어 normalization과 protected span 처리를 correction 전에 적용할 수 있게 만든다.

dep: P3.5
branch: `wbs/P4-normalization-protection`
spec: `docs/dev/specs/p4-normalization-protection.md`
plan: `docs/dev/plans/p4-normalization-protection-plan.md`
loop level: Level 2

예상 산출물:

- `src/whisper_wfst/normalize.py`
- `src/whisper_wfst/protect.py`
- `tests/test_unicode.py`
- `tests/test_protected_spans.py`

ops 승격 후보:

- none

범위:

- Unicode NFC normalization
- normalized duplicate key 생성
- 전화번호, 주민번호, 계좌번호, 카드번호, 증권번호, 금액, 날짜, URL, 영문 코드 placeholder 보호
- 외부 annotation으로 주입된 이름 span 보호
- restore roundtrip

비범위:

- 형태소 분석
- 이름 인식 NER
- 의미를 바꾸는 텍스트 정규화

완료 기준:

- NFC/NFD 한글이 같은 key로 dedupe됨
- protected span 내부 correction이 발생하지 않음
- 이름은 자동 탐지하지 않고 external span으로 들어온 경우만 보호됨
- restore 후 원래 protected span이 보존됨

### P5. Synthetic N-best WFST Composition MVP - todo L

목표: 음성 없이 synthetic N-best artifact와 correction rule로 weighted composition 결과를 생성한다.

dep: P4
branch: `wbs/P5-synthetic-nbest-wfst`
spec: `docs/dev/specs/p5-synthetic-nbest-wfst.md`
plan: `docs/dev/plans/p5-synthetic-nbest-wfst-plan.md`
loop level: Level 2

예상 산출물:

- `src/whisper_wfst/nbest_acceptor.py`
- `src/whisper_wfst/correction_wfst.py`
- `src/whisper_wfst/compose.py`
- `tests/test_nbest_acceptor.py`
- `tests/test_correction_wfst.py`
- `tests/test_composition.py`
- `tests/test_overlapping_rules.py`

ops 승격 후보:

- none

범위:

- N-best weighted acceptor 생성
- correction WFST 생성
- `A_x o C` composition
- shortest path output
- identity cost 0
- obligatory correction
- optional keep/correct branch
- deterministic overlapping rule order: `length desc -> priority desc -> total cost -> stable rule_id`
- length mismatch correction
- no-path fallback

비범위:

- HF extraction
- CT2/faster-whisper extraction
- real audio inference
- evaluation report generation

완료 기준:

- `손해보혐 -> 손해보험` test 통과
- `혐오`가 `험오`로 바뀌지 않음
- 겹치는 rule에서 deterministic order가 test로 고정됨
- optional rule에서 identity path가 keep cost를 무료 우회하지 못함
- cdrewrite 구현이 optional identity bypass test를 통과하지 못하면 phrase trie 기반 leftmost-longest rule engine으로 전환함
- rule 미적용 시 lowest ASR cost hypothesis가 유지됨
- composition failure fallback이 trace에 남음

### P6. Correction Safety / Trace / Domain Gating - todo L

목표: overcorrection 방지와 자유대화 보호 정책을 구현한다.

dep: P5
branch: `wbs/P6-correction-safety-trace-domain-gating`
spec: `docs/dev/specs/p6-correction-safety-trace-domain-gating.md`
plan: `docs/dev/plans/p6-correction-safety-trace-domain-gating-plan.md`
loop level: Level 2

예상 산출물:

- `src/whisper_wfst/trace.py`
- `src/whisper_wfst/safety.py`
- `configs/correction.yaml`
- `tests/test_margin.py`
- `tests/test_domain_gating.py`
- `tests/test_trace.py`
- `docs/reports/probes/free_talk_safety_smoke.md`

ops 승격 후보:

- none

범위:

- correction margin
- domain gate on/off
- fixed safety order: protect spans -> domain gate -> compose -> margin decision -> trace
- optional rule keep/correct decision trace
- risky rule config
- free-talk fixture에서 rule application rate 측정
- correction result JSON trace

비범위:

- production speaker/channel classifier
- 상담원/고객 diarization
- domain LM or phrase acceptor

완료 기준:

- domain gate off이면 correction이 적용되지 않음
- domain gate off이면 obligatory rule도 적용되지 않음
- free-talk fixture에서 unexpected correction이 0 또는 명시된 허용 범위임
- margin이 작은 correction을 차단함
- trace가 source hypothesis rank, before/after, costs, rule ids를 포함함

### P7. Hugging Face Whisper N-best Extractor - todo L

목표: HF Transformers Whisper에서 N-best text와 score를 artifact로 저장한다.

dep: P6
branch: `wbs/P7-hf-nbest-extractor`
spec: `docs/dev/specs/p7-hf-nbest-extractor.md`
plan: `docs/dev/plans/p7-hf-nbest-extractor-plan.md`
loop level: Level 2

예상 산출물:

- `src/whisper_wfst/hf_extractor.py`
- `scripts/extract_hf_nbest.py`
- `configs/hf.yaml`
- `tests/test_hf_extractor.py`
- `docs/reports/probes/hf_nbest_smoke.md`

ops 승격 후보:

- none

범위:

- `num_beams`
- `num_return_sequences`
- `return_dict_in_generate`
- `output_scores`
- `compute_transition_scores`
- forced language/task token score handling 확인
- normalized duplicate count report
- ranking sanity test
- N-best oracle / domain oracle risk flag report
- short audio smoke

비범위:

- long-form segmentation
- GPU performance optimization
- teacher-force rescore

완료 기준:

- short audio 또는 mocked generation에서 N-best artifact 생성 가능
- raw score, decoder score, decode config가 artifact에 기록됨
- `score_source`, `score_is_logprob`, `length_penalty`, `asr_cost`가 artifact에 기록됨
- unique hypothesis count가 report에 남음
- domain oracle hit와 N-best oracle 개선 여부가 P10 진입 risk flag로 남음
- score 해석의 residual uncertainty가 문서화됨

### P8. HF N-best Targetability Probe - todo M

목표: HF N-best artifact와 reference를 사용해 N-best에 correction 가능성이 실제로 있는지 확인한다.

dep: P3.5, P7
branch: `wbs/P8-hf-nbest-targetability`
spec: `docs/dev/specs/p8-hf-nbest-targetability.md`
plan: `docs/dev/plans/p8-hf-nbest-targetability-plan.md`
loop level: Level 1

예상 산출물:

- `scripts/probe_targetability.py`
- `docs/reports/probes/nbest_targetability_probe.md`
- `tests/test_targetability_probe.py`

ops 승격 후보:

- none

범위:

- HF N-best artifact와 reference text alignment
- unique hypothesis count
- top1 vs N-best oracle CER/WER
- domain term oracle accuracy
- 정답 surface가 N-best 안에 있는 비율
- seed rule의 wrong surface가 top1에 있는 비율
- seed rule의 wrong surface가 N-best 안에 있는 비율

비범위:

- automatic rule promotion
- LLM 기반 rule 생성
- rule mining
- correction engine을 사용한 top1+rules vs N-best+rules 비교

완료 기준:

- targetability report가 unique count, N-best oracle, domain oracle, seed rule wrong surface 비율을 포함함
- targetability가 낮으면 P10은 negative evidence run으로만 진행하거나 범위를 재검토함
- final eval leakage 금지 정책이 report에 반영됨

### P9. Evaluation Harness - todo L

목표: correction 효과와 risk를 offline metric으로 비교한다.

dep: P5, P6
branch: `wbs/P9-evaluation-harness`
spec: `docs/dev/specs/p9-evaluation-harness.md`
plan: `docs/dev/plans/p9-evaluation-harness-plan.md`
loop level: Level 2

예상 산출물:

- `docs/ops/evaluation.md`
- `docs/ops/evaluation-calibration-design.md`
- `src/whisper_wfst/evaluate.py`
- `scripts/evaluate_corrections.py`
- `tests/test_evaluate.py`
- `tests/test_evaluation_manifest.py`
- `docs/reports/probes/evaluation_baseline.md`

ops 승격 후보:

- `docs/ops/evaluation.md`: P9 metric/report contract가 current evaluation 기준으로 충분하면 승격

범위:

- CER/WER
- domain term accuracy
- N-best oracle CER/WER
- domain term oracle accuracy
- correction precision/recall
- overcorrection rate
- free-talk correction rate
- free-talk overcorrection rate
- unique hypothesis count
- latency summary fields
- evaluation input manifest schema: `segment_id`, `audio_ref`, `source_wav`, `source_start`, `source_end`, `split`, `channel`, `is_script_span`, `is_free_talk`, `ref_text`, `domain_terms`, `allowed_rules`
- comparison B uses rank0-only artifact through the same correction engine

비범위:

- subjective transcript quality review
- production monitoring dashboard

완료 기준:

- synthetic prediction/reference pair로 metric tests 통과
- evaluation input manifest validation이 통과함
- unavailable metric은 `not_applicable`로 남음
- A/B/C/D comparison report format이 고정됨
- top1 + correction 비교군은 rank0 단일 hypothesis로 truncate한 artifact로 정의됨
- free-talk safety metric이 별도로 출력됨

### P10. End-to-End Offline MVP Run - todo L

목표: 실제 또는 reviewed sample audio에서 N-best extraction부터 correction/evaluation까지 한 번에 재현한다.

dep: P7, P8, P9
branch: `wbs/P10-offline-mvp-run`
spec: `docs/dev/specs/p10-offline-mvp-run.md`
plan: `docs/dev/plans/p10-offline-mvp-run-plan.md`
loop level: Level 2

예상 산출물:

- `scripts/run_offline_pipeline.py`
- `docs/reports/experiments/offline_mvp_run.md`
- `docs/reports/experiments/offline_mvp_manifest.json`
- ignored artifacts under `outputs/`

ops 승격 후보:

- none

범위:

- selected audio set
- HF N-best artifact generation
- P8 targetability gate 확인
- correction result generation
- trace generation
- A/B/C/D evaluation
- artifact checksums

비범위:

- large-scale batch processing
- serving API
- model fine-tuning

완료 기준:

- all input/output artifact paths and checksums are recorded
- P8 targetability conclusion과 N-best oracle/domain oracle risk flag가 report에 반영됨
- corrected output and trace are reproducible from committed config + ignored artifacts
- repository contains reports/manifests only, not large artifacts
- no full-quality production claim is made

### P11. Calibration / Rule Tuning - todo M

목표: lambda, margin, rule cost, risky rule policy를 evaluation 결과로 조정한다.

dep: P10
branch: `wbs/P11-calibration-rule-tuning`
spec: `docs/dev/specs/p11-calibration-rule-tuning.md`
plan: `docs/dev/plans/p11-calibration-rule-tuning-plan.md`
loop level: Level 2

예상 산출물:

- `docs/reports/experiments/correction_calibration.md`
- updated `configs/correction.yaml`
- optional tuned rule CSV

ops 승격 후보:

- `configs/correction.yaml`: calibration 결과가 final eval 전 freeze 기준으로 충분하면 승격

범위:

- lambda sweep
- margin sweep
- `num_beams` / `num_return_sequences` sweep review
- corr_cost / keep_cost sweep
- rule policy sweep: safe_only, safe_optional_medium, diagnostic_all
- domain gate policy sweep
- hard gate 기반 best config selection
- final eval 전 config freeze
- optional/obligatory mode review
- high-risk rule disabled/optional decision
- free-talk regression check

비범위:

- automatic rule mining
- domain LM addition

완료 기준:

- chosen lambda/margin이 report 근거와 함께 기록됨
- chosen `num_beams`/`num_return_sequences`와 rule/gate policy가 report 근거와 함께 기록됨
- hard gate를 통과한 config 중 best를 선택함
- final eval 전에 config/rule/artifact checksum이 freeze됨
- domain metric 개선과 free-talk risk가 함께 보고됨
- tuning 후 regression tests 통과

### P12. Optional Teacher-Force Rescore Design - todo M

목표: N-best + WFST만으로 부족할 경우 teacher-forcing rescore를 추가할지 판단한다.

dep: P10, P11
branch: `wbs/P12-teacher-force-rescore-design`
spec: `docs/dev/specs/p12-teacher-force-rescore-design.md`
plan: `docs/dev/plans/p12-teacher-force-rescore-design-plan.md`
loop level: Level 1

예상 산출물:

- `docs/dev/specs/p12-teacher-force-rescore-design.md`
- `docs/dev/plans/p12-teacher-force-rescore-design-plan.md`

ops 승격 후보:

- none

범위:

- corrected candidate M개 생성
- Whisper teacher-forcing score feasibility
- latency/quality trade-off
- HF-only MVP 여부

비범위:

- P10 MVP scope 변경
- rescore implementation without design approval

완료 기준:

- rescore가 필요한지 yes/no 판단이 근거와 함께 남음
- 구현한다면 후속 WBS input/output/metric이 정의됨

### P13. PoC Go / No-Go Report - todo M

목표: MVP 결과를 종합해 다음 단계 진행 여부를 판단한다.

dep: P10, P11, optional P12
branch: `wbs/P13-poc-go-no-go`
spec: `docs/dev/specs/p13-poc-go-no-go.md`
plan: `docs/dev/plans/p13-poc-go-no-go-plan.md`
loop level: Level 1

예상 산출물:

- `docs/reports/experiments/poc_go_no_go.md`
- optional ADR under `docs/dev/decisions/`

ops 승격 후보:

- none

판정 질문:

- N-best 안에 domain correction 기회가 충분히 있었는가?
- N-best + WFST가 top1 correction보다 나았는가?
- overcorrection rate가 허용 가능한가?
- 자유대화 영향이 제한적인가?
- HF runtime PoC로 충분한가?
- Pynini/OpenFST 운영 리스크가 감당 가능한가?
- teacher-force rescore가 필요한가?

완료 기준:

- Go / No-Go / Continue-with-scope-change 중 하나가 명시됨
- unresolved risk와 후속 WBS가 정리됨
- 결과가 과장 없이 artifact/report 근거에 연결됨

## 4. 현재 다음 액션

1. P2 FST Backend Feasibility를 시작한다.
2. Pynini/OpenFST 설치와 Unicode utf8 token type smoke를 확인한다.
3. `손해보혐 -> 손해보험` compose/shortest path smoke test를 만든다.
