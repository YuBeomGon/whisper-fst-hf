# WBS 2.0 - Real HF Dataset / Pair Mining Evaluation

최종 갱신: 2026-06-26

## 1. 목적

WBS 1.0은 synthetic/mock 기반 scaffold와 안전장치 구현을 완료했다. WBS 2.0은 실제 AIG 상담원 채널
데이터를 사용해 다음 질문에 답한다.

1. 실제 audio/text pair를 안정적으로 만들 수 있는가?
2. 기존 SRT run과 label에서 보험 상담 도메인 `wrong -> right` pair 후보를 만들 수 있는가?
3. 실제 HF Whisper N-best 20개 안에 교정 가능한 후보가 살아 있는가?
4. leakage-safe rule로 CER/WER/domain accuracy를 개선할 수 있는가?
5. overcorrection과 자유대화 regression을 통제할 수 있는가?

## 2. 기준 문서

- 전체 설계: `docs/dev/specs/project-design.md`
- WBS 1.0 완료 이력: `docs/wbs.md`
- Pair mining 설계: `docs/dev/specs/wbs-2.0/misrecognition-pair-mining-design.md`
- 운영 원칙: `docs/ops/governance.md`
- 평가/캘리브레이션 원칙: `docs/ops/evaluation-calibration-design.md`
- 도메인/data reference: `docs/assets/aig_domain_data_context.md`

## 3. 범위

### 3.1 In Scope

- `_l` 상담원 채널 중심 audio/text inventory
- `_l.txt` label parser v2와 normalization
- 너무 짧은 label 제외
- `[]` tag 제거와 protected span 처리
- `<wrong>/<right>`류 markup에서 오른쪽 정인식 추출
- 모든 `_l.srt` run inventory와 annotation matching
- 기존 SRT run 전체 기반 `wrong -> right` pair candidate dictionary 생성
- support count 분리: run/file/batch/variant
- human review 가능한 pair candidate CSV
- leakage-safe rule seed 생성
- HF Transformers Whisper real audio N-best extraction
- N-best targetability와 pair coverage 평가
- correction 적용 전/후 CER/WER/domain accuracy 비교
- calibration sweep과 safety gate

### 3.2 Out of Scope

- CTranslate2/faster-whisper runtime integration
- production serving
- large artifact commit
- rule 자동 승인
- LLM 기반 rule generation
- final holdout pair를 rule seed로 사용하는 것

## 4. 공통 실행 Loop

각 phase는 동일한 loop로 진행한다.

```text
1. main 최신 상태 확인
2. phase branch 생성: wbs/v2/Pxx-*
3. phase design spec 작성
4. implementation plan 작성
5. 구현 또는 문서화
6. 테스트/검증
7. review 문서 작성
8. DoD 확인
9. commit
10. main fast-forward merge
11. push
12. docs/status.md, docs/CHANGELOG.md 갱신
```

문제 발생 시 phase 중간에서 멈추고 blocker report를 남긴다.

## 5. Data Governance

원문 audio, full transcript, full SRT text, large HF N-best artifact는 commit하지 않는다.

commit 가능:

- parser code
- schema
- synthetic/minimal fixture
- aggregate report
- checksum manifest
- sample CSV with redacted/minimal rows

local/ignored output:

```text
outputs/wbs-2.0/
outputs/pair_mining/
outputs/hf_nbest_real/
outputs/eval_real/
```

## 6. Split / Leakage 원칙

WBS 2.0은 파일 단위 split을 먼저 고정한다.

| Split | Purpose | Rule Usage |
| --- | --- | --- |
| `rule_mining` | pair 후보 생성 | allowed |
| `dev_review` | rule review/calibration | allowed with audit |
| `eval_holdout` | 최종 성능 확인 | rule seed로 사용 금지 |

모든 SRT run에서 후보를 만들 수는 있지만, `eval_holdout`에만 존재하는 pair는 rule seed로 승격하지 않는다.

## 7. Phase Index

| Phase | Status | Branch |
| --- | --- | --- |
| P14 Audio/Text Source Inventory | pending | `wbs/v2/P14-audio-text-source-inventory` |
| P15 Label Parser / Normalization v2 | pending | `wbs/v2/P15-label-parser-normalization-v2` |
| P16 SRT Run Inventory / Matching | pending | `wbs/v2/P16-srt-run-inventory-matching` |
| P17 Misrecognition Pair Mining | pending | `wbs/v2/P17-misrecognition-pair-mining` |
| P18 Pair Review / Rule Source Audit v2 | pending | `wbs/v2/P18-pair-review-rule-source-audit-v2` |
| P19 Real HF N-best Extraction | pending | `wbs/v2/P19-real-hf-nbest-extraction` |
| P20 Real N-best Targetability | pending | `wbs/v2/P20-real-nbest-targetability` |
| P21 Leakage-safe Correction Evaluation | pending | `wbs/v2/P21-leakage-safe-correction-eval` |
| P22 Calibration / Safety Sweep | pending | `wbs/v2/P22-calibration-safety-sweep` |
| P23 PoC v2 Go / No-Go | pending | `wbs/v2/P23-poc-v2-go-no-go` |

---

## P14. Audio/Text Source Inventory

목표: `_l` audio와 `_l` label을 file stem 기준으로 매칭하고, WBS 2.0에서 사용할 split manifest를 만든다.

dep: WBS 1.0, pair mining design

branch: `wbs/v2/P14-audio-text-source-inventory`

spec: `docs/dev/specs/wbs-2.0/p14-audio-text-source-inventory.md`

plan: `docs/dev/plans/wbs-2.0/p14-audio-text-source-inventory-plan.md`

outputs:

- `src/whisper_wfst/source_inventory.py`
- `scripts/inventory_audio_text_sources.py`
- `docs/reports/audits/audio_text_source_inventory.md`
- `outputs/wbs-2.0/source_inventory/source_inventory.json` ignored
- `outputs/wbs-2.0/source_inventory/split_manifest.json` ignored

scope:

- scan `/data/MyProject/stt/aig/stt-engine/shared/annotations/**/*_l.txt`
- scan available `_l.wav` or source audio locations
- match by source stem/channel
- record batch, source_wav, label_path, channel, duration if available
- classify exclusions: missing_audio, missing_label, too_short_label, bad_format, duplicate_stem
- create file-level split: `rule_mining`, `dev_review`, `eval_holdout`

tests:

- unit test for stem/channel matching
- unit test for split manifest validation
- fixture with missing audio/label cases

DoD:

- `_l` label/audio match counts are reported
- exclusion reasons are explicit
- split manifest exists as local ignored artifact with checksum in report
- no raw transcript/audio content is committed

stop conditions:

- actual `_l` audio cannot be located
- label/audio stem matching is ambiguous for too many files
- split cannot be made without leakage risk

---

## P15. Label Parser / Normalization v2

목표: 47개 `_l.txt` label format variation을 처리하는 parser와 비교용 normalized reference text를 만든다.

dep: P14

branch: `wbs/v2/P15-label-parser-normalization-v2`

spec: `docs/dev/specs/wbs-2.0/p15-label-parser-normalization-v2.md`

plan: `docs/dev/plans/wbs-2.0/p15-label-parser-normalization-v2-plan.md`

outputs:

- `src/whisper_wfst/label_parser.py`
- `scripts/audit_label_formats.py`
- `docs/reports/audits/label_format_audit.md`
- `data/label_parser_cases.sample.jsonl`

scope:

- parse 30초 index block
- handle no-index fallback
- detect non-monotonic or duplicate index candidates
- exclude too-short labels
- remove square tags from comparison text
- protect `[NAME]`, `[CONTACT]`, `[ADDR]` spans
- parse `<wrong>/<right>`류 markup and keep right-side correct text
- remove unrecognized standalone `<...>` from comparison text
- report `[SCRIPT_START]` / `[SCRIPT_END]` imbalance

tests:

- normal index block
- no-index fallback
- numeric text not treated as index
- short label exclusion
- square tag removal
- angle correction right-side preservation
- protected span exclusion

DoD:

- all known `_l.txt` format classes are represented in audit report
- parser produces stable blocks with approximate time ranges
- normalized reference text never contains protected personal spans
- no raw sensitive label text is committed

---

## P16. SRT Run Inventory / Matching

목표: 모든 `_l.srt` run을 inventory하고 label/source file과 매칭한다.

dep: P14, P15

branch: `wbs/v2/P16-srt-run-inventory-matching`

spec: `docs/dev/specs/wbs-2.0/p16-srt-run-inventory-matching.md`

plan: `docs/dev/plans/wbs-2.0/p16-srt-run-inventory-matching-plan.md`

outputs:

- `src/whisper_wfst/srt_inventory.py`
- `scripts/inventory_srt_runs.py`
- `docs/reports/audits/srt_run_inventory.md`
- `outputs/wbs-2.0/srt_inventory/srt_run_inventory.json` ignored

scope:

- scan `/data/MyProject/stt/aig/stt-engine/shared/debug/output/**/*_l.srt`
- parse run_id, variant, source_stem, channel
- validate SRT timestamp blocks
- match SRT to label inventory
- compute run coverage by label file
- identify duplicated/partial/smoke runs
- keep all run sources for pair mining, but tag run class

tests:

- SRT parser fixture
- run path metadata extraction
- label matching fixture
- malformed SRT handling

DoD:

- all `_l.srt` paths are cataloged
- label match coverage is reported by run
- no full SRT text is committed
- inventory distinguishes full left runs from smoke/partial runs

---

## P17. Misrecognition Pair Mining

목표: label reference와 모든 matched SRT hypothesis를 비교해 `wrong -> right` pair candidate dictionary를 만든다.

dep: P15, P16

branch: `wbs/v2/P17-misrecognition-pair-mining`

spec: `docs/dev/specs/wbs-2.0/p17-misrecognition-pair-mining.md`

plan: `docs/dev/plans/wbs-2.0/p17-misrecognition-pair-mining-plan.md`

outputs:

- `src/whisper_wfst/pair_mining.py`
- `scripts/mine_misrecognition_pairs.py`
- `docs/reports/audits/misrecognition_pair_mining.md`
- `data/pair_candidates.sample.csv`
- `outputs/pair_mining/pair_candidates.csv` ignored
- `outputs/pair_mining/pair_candidates.jsonl` ignored

scope:

- rough align label 30초 blocks with SRT timestamp windows
- sequence-align normalized ref/hyp text
- extract phrase-level wrong/right diff candidates
- filter too-short/too-long/digit-only/protected-span pairs
- classify confidence and risk flags
- aggregate pair support by run/file/batch/variant
- generate reviewable candidate CSV

tests:

- block alignment fixture
- diff phrase extraction fixture
- protected span rejection
- support count aggregation
- duplicate run does not inflate file support

DoD:

- pair candidates are generated from all matched SRT runs
- support counts are separated correctly
- low-confidence candidates are not auto-promoted
- sample CSV is redacted/minimal and safe to commit

stop conditions:

- alignment confidence is too low to generate useful phrase candidates
- candidate volume is dominated by sentence-level mismatches
- protected/personal text leaks into candidate output

---

## P18. Pair Review / Rule Source Audit v2

목표: pair candidate를 review/audit해서 leakage-safe `correction_rules_seed.csv`를 만든다.

dep: P14, P17

branch: `wbs/v2/P18-pair-review-rule-source-audit-v2`

spec: `docs/dev/specs/wbs-2.0/p18-pair-review-rule-source-audit-v2.md`

plan: `docs/dev/plans/wbs-2.0/p18-pair-review-rule-source-audit-v2-plan.md`

outputs:

- `src/whisper_wfst/pair_review.py`
- `scripts/audit_pair_sources.py`
- `docs/reports/audits/pair_rule_source_audit_v2.md`
- `data/pair_review_schema.csv`
- `data/correction_rules_seed_v2.sample.csv`
- `outputs/pair_mining/correction_rules_seed_v2.csv` ignored

scope:

- apply split/leakage policy
- mark `rule_mining`, `dev_review`, `eval_holdout` provenance
- classify candidates: obligatory, optional, reject, needs_review
- keep support_file_count and support_batch_count as promotion signals
- reject test-only/eval-only candidates
- produce seed rule CSV for downstream evaluation

tests:

- eval-only candidate cannot become seed rule
- protected risk candidate is rejected
- optional/obligatory schema validation
- support count threshold behavior

DoD:

- seed rules are leakage-safe
- every seed rule has provenance
- every rejected high-risk candidate has a reason
- final eval source is not used for rule generation

---

## P19. Real HF N-best Extraction

목표: 실제 `_l` audio를 HF Transformers Whisper에 넣어 beam 20 / num hypotheses 20 artifact를 만든다.

dep: P14, P15

branch: `wbs/v2/P19-real-hf-nbest-extraction`

spec: `docs/dev/specs/wbs-2.0/p19-real-hf-nbest-extraction.md`

plan: `docs/dev/plans/wbs-2.0/p19-real-hf-nbest-extraction-plan.md`

outputs:

- `src/whisper_wfst/hf_audio_extractor.py`
- `scripts/extract_real_hf_nbest.py`
- `configs/hf-real.yaml`
- `docs/reports/experiments/real_hf_nbest_extraction.md`
- `outputs/hf_nbest_real/*.jsonl` ignored

scope:

- load matched audio/text source manifest
- run HF Whisper only, not CT2
- use `num_beams=20`, `num_return_sequences=20`
- store N-best text, scores, decode config, model/runtime metadata
- normalize and de-duplicate hypotheses
- checkpoint/resume extraction
- small smoke first, then selected split

tests:

- mocked HF runtime adapter test
- artifact schema validation
- duplicate hypothesis count behavior
- resume manifest behavior

DoD:

- real audio smoke artifact is generated or blocker is documented
- score metadata is preserved
- unique hypothesis distribution is reported
- no large artifact is committed

stop conditions:

- HF model/runtime cannot load
- audio format cannot be fed to HF safely
- beam 20 / return 20 is infeasible on available hardware

---

## P20. Real N-best Targetability

목표: 실제 HF N-best 안에 정답 또는 pair 기반 교정 가능 후보가 살아 있는지 측정한다.

dep: P18, P19

branch: `wbs/v2/P20-real-nbest-targetability`

spec: `docs/dev/specs/wbs-2.0/p20-real-nbest-targetability.md`

plan: `docs/dev/plans/wbs-2.0/p20-real-nbest-targetability-plan.md`

outputs:

- `scripts/probe_real_targetability.py`
- `docs/reports/experiments/real_nbest_targetability.md`
- `outputs/hf_nbest_real/targetability_report.json` ignored

scope:

- compute top1 CER/WER and N-best oracle CER/WER
- compute pair coverage: wrong surface in top1, right surface in N-best
- compute unique hypothesis count distribution
- separate rule_mining/dev_review/eval_holdout metrics
- report whether P21 evaluation should proceed

tests:

- targetability fixture with right candidate present
- fixture where all N-best variants are duplicates
- split-aware metric aggregation

DoD:

- real N-best oracle metrics are reported
- pair coverage is reported by split
- P21 proceed/no-proceed recommendation is explicit

stop conditions:

- N-best oracle has no meaningful improvement over top1
- right-side correction candidates are absent from N-best for target pairs
- artifacts are too incomplete for evaluation

---

## P21. Leakage-safe Correction Evaluation

목표: leakage-safe rules를 실제 HF N-best에 적용해 correction 전후 성능을 비교한다.

dep: P18, P20

branch: `wbs/v2/P21-leakage-safe-correction-eval`

spec: `docs/dev/specs/wbs-2.0/p21-leakage-safe-correction-eval.md`

plan: `docs/dev/plans/wbs-2.0/p21-leakage-safe-correction-eval-plan.md`

outputs:

- `scripts/evaluate_real_corrections.py`
- `docs/reports/experiments/real_correction_eval.md`
- `outputs/eval_real/correction_eval.json` ignored
- `outputs/eval_real/correction_traces.jsonl` ignored

scope:

- run baseline top1 metrics
- run top1+rules baseline
- run N-best+rules correction
- compute CER/WER/domain term accuracy
- compute correction precision/recall
- compute overcorrection rate
- evaluate script span and non-script/free-talk segments separately when metadata exists
- preserve correction trace for review

tests:

- A/B/C/D metric fixture
- overcorrection fixture
- domain gate fixture with real-style manifest
- trace schema validation

DoD:

- eval_holdout metric table is reported
- N-best+rules is compared against top1 and top1+rules
- overcorrection is reported, not hidden
- no production-quality claim is made without passing gates

stop conditions:

- correction does not improve domain accuracy
- CER/WER regresses beyond hard gate
- free-talk/non-script regression exceeds hard gate

---

## P22. Calibration / Safety Sweep

목표: correction cost, margin, optional rule policy, gating threshold를 바꿔 best config를 선택한다.

dep: P21

branch: `wbs/v2/P22-calibration-safety-sweep`

spec: `docs/dev/specs/wbs-2.0/p22-calibration-safety-sweep.md`

plan: `docs/dev/plans/wbs-2.0/p22-calibration-safety-sweep-plan.md`

outputs:

- `scripts/run_real_calibration_sweep.py`
- `configs/correction-v2.yaml`
- `docs/reports/experiments/real_calibration_sweep.md`
- `outputs/eval_real/calibration_sweep.csv` ignored

scope:

- sweep lambda/correction_cost/margin
- compare optional vs obligatory rule behavior
- enforce hard gates before selecting best
- freeze selected config with checksum
- list rejected configs and reasons

tests:

- hard gate filtering
- best config tie-breaker
- config checksum generation

DoD:

- selected config is reproducible
- rejected configs are auditable
- best config is not selected solely by domain accuracy if CER/free-talk regresses

---

## P23. PoC v2 Go / No-Go

목표: 실제 data 기반 evidence로 다음 단계 진행 여부를 결정한다.

dep: P20, P21, P22

branch: `wbs/v2/P23-poc-v2-go-no-go`

spec: `docs/dev/specs/wbs-2.0/p23-poc-v2-go-no-go.md`

plan: `docs/dev/plans/wbs-2.0/p23-poc-v2-go-no-go-plan.md`

outputs:

- `docs/reports/experiments/poc_v2_go_no_go.md`
- `docs/dev/decisions/0002-poc-v2-decision.md`

decision candidates:

- `Go`: real HF N-best + correction improves target metrics within safety gates
- `Continue-with-scope-change`: targetability or correction is promising but incomplete
- `No-Go`: N-best targetability or safety gates fail

DoD:

- decision is tied to real data evidence
- unresolved risks are explicit
- next WBS or production hardening plan is scoped
- WBS 2.0 is marked complete or blocked

## 8. Global Completion Criteria

WBS 2.0 is complete when:

- audio/text source inventory is established
- label and SRT parsing are validated
- pair candidates are mined from all matched `_l.srt` runs
- seed rules are leakage-safe
- real HF N-best extraction has run or produced a clear blocker
- real targetability is measured
- correction evaluation is run with safety gates
- calibration decision is documented
- PoC v2 decision is recorded

If real HF extraction cannot run, WBS 2.0 may stop early with a blocker report instead of continuing synthetic-only.
