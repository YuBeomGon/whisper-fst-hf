# GPT WBS Feedback Review

날짜: 2026-06-26

문서 등급: design review record

검토 대상:

- `docs/wbs.md`
- `docs/dev/specs/project-design.md`
- `docs/ops/evaluation-calibration-design.md`
- `docs/reports/audits/wfst-domain-feasibility-research.md`
- `scripts/archive_project_snapshot.py`
- `pyproject.toml`

## 1. 결론

GPT 리뷰의 핵심 방향은 대체로 맞다.

현재 설계는 HF-only PoC, N-best targetability, free-talk safety, calibration/final split 같은 큰 방향은
잡혀 있다. 그러나 실제 성능 주장 리스크를 줄이려면 다음 보강이 필요하다.

우선순위:

1. P2에서 Pynini/OpenFST feasibility를 실제 한글 compose 수준까지 검증한다.
2. P3 뒤에 Rule Source Audit / Seed Rule Review phase를 추가한다.
3. evaluation manifest를 domain gate에 필요한 필드까지 확장한다.
4. P8은 correction engine 없이 가능한 순수 targetability probe로 좁힌다.
5. archive snapshot에 `data/`를 포함하되 large/generated subtree를 제외한다.
6. P5에서 optional rule identity bypass test와 fallback 정책을 강하게 둔다.

## 2. 항목별 판단

| Item | 판단 | 이유 |
| --- | --- | --- |
| Rule Source Audit phase 부족 | 맞음 | feasibility report에는 권고가 있으나 WBS phase로는 빠져 있다. Rule provenance 없이 `correction_rules.csv`를 만들면 leakage 위험이 크다. |
| evaluation manifest와 domain gate 필드 불일치 | 맞음 | WBS manifest는 `channel`, `is_script_span`, `source_wav`, time span이 없다. 그런데 gate policy는 `_l` 채널과 script/domain span을 필요로 한다. |
| P8 dependency 애매함 | 맞음 | 현재 P8 범위의 `top1+rules 대비 N-best+rules`는 rule matcher/correction engine 없이는 정확히 계산하기 어렵다. |
| archive script에 `data/` 누락 | 맞음 | 현재 `INCLUDE_DIRS`에 `data`가 없다. 이후 `data/correction_rules.csv`가 생기면 snapshot에서 빠진다. |
| Pynini/OpenFST가 첫 기술 blocker | 맞음 | P2를 둔 판단은 맞다. 다만 import smoke만으로 부족하고 한글 token/compose/shortest path까지 봐야 한다. |
| Python version 민감성 | 조건부로 맞음 | `requires-python = ">=3.11"`은 상한이 없어 3.13 선택 가능성이 있다. 현재 실행은 3.12였지만 FST 의존성은 P2에서 3.11/3.12 중심으로 확인하는 편이 안전하다. |
| `cdrewrite` optional rule identity bypass 위험 | 맞음 | 현재 WBS에 identity bypass test는 있지만, 실패 시 phrase trie/leftmost-longest fallback 정책은 더 명확히 해야 한다. |
| P0/P1은 괜찮고 다음은 P2 | 맞음 | 현재 P0/P1은 done이고 다음 기술 blocker가 P2다. |

## 3. 최종 정정안

### 3.1 WBS: Rule Source Audit phase 추가

P3 뒤, P4 전에 다음 phase를 추가하는 것이 좋다. 번호는 기존 phase 재번호 변경을 피하려면 `P3.5`로 둔다.

```text
### P3.5. Rule Source Audit / Seed Rule Review - todo M

목표: correction rule seed가 어떤 데이터에서 왔는지 검증하고, final eval leakage 없이 안전한 seed만 분리한다.

dep: P3

예상 산출물:

- docs/reports/probes/rule_source_audit.md
- data/correction_rules_seed.csv
- tests/test_rule_source_audit.py

범위:

- dictionary_registry / aligned_segments / phrase-bias 결과의 rule source 정리
- rule_id, wrong, right, source, provenance, support, source_wav, segment_id 기록
- final eval 유래 여부 표시
- free-talk risk label
- obligatory / optional / disabled 후보 분류
- 긴 script span, number/PII, low-support rule 보류

완료 기준:

- seed rule마다 provenance와 support가 기록됨
- final eval 유래 rule은 final claim에 사용하지 않도록 표시됨
- `safe_only` seed CSV가 생성됨
- high-risk rule은 disabled 또는 optional 후보로만 남음
```

이 phase가 없으면 P3의 `data/correction_rules.csv`가 너무 빨리 production rule처럼 취급될 수 있다.

### 3.2 WBS/P9: evaluation manifest 확장

현재 manifest:

```text
segment_id, ref_text, split, is_free_talk, domain_terms, audio_ref, allowed_rules
```

권장 manifest:

```text
segment_id
audio_ref
source_wav
source_start
source_end
split
channel
is_script_span
is_free_talk
ref_text
domain_terms
allowed_rules
```

이유:

- `agent_channel_only` gate에는 `channel`이 필요하다.
- `script_or_domain_span_only` gate에는 `is_script_span`이 필요하다.
- split leakage 검증에는 `source_wav`가 필요하다.
- trace와 segment-level 재현에는 `source_start`, `source_end`가 필요하다.

### 3.3 WBS/P8: 순수 targetability probe로 좁히기

P8은 correction engine 평가가 아니라 "N-best에 교정 가능성이 있느냐"만 본다.

유지할 항목:

- unique hypothesis count
- top1 vs N-best oracle CER/WER
- domain term oracle accuracy
- 정답 surface가 N-best 안에 있는 비율
- seed rule의 wrong surface가 top1 또는 N-best 안에 있는 비율

제거하거나 P10/P11로 이동할 항목:

```text
top1+rules 대비 N-best+rules가 추가로 고칠 수 있는 segment 비율
```

이 항목은 rule matcher 또는 correction engine이 필요하므로 P8에 두면 dependency가 불명확해진다.

권장 dependency:

```text
P8 dep: P3.5, P7
```

P8은 P5/P6 없이도 실행 가능해야 한다.

### 3.4 Archive script: `data/` 포함

현재 `scripts/archive_project_snapshot.py`의 `INCLUDE_DIRS`는 `data`를 포함하지 않는다.

권장:

```python
INCLUDE_DIRS = (
    "docs",
    "configs",
    "data",
    "src",
    "tests",
    "scripts",
)
```

단, exclude는 유지 또는 보강한다.

```text
data/raw/
data/processed/
outputs/
*.wav
*.mp3
*.flac
*.jsonl.gz
```

테스트도 `data/correction_rules.csv`는 포함되고 `data/raw/**`, `data/processed/**`는 제외되는지 확인해야 한다.

### 3.5 P2: Pynini/OpenFST smoke 강화

P2는 단순 import 성공으로 끝내지 않는다.

필수 smoke:

1. Pynini import
2. utf8 token type에서 한글 acceptor 생성
3. `손해보혐 -> 손해보험` cross 생성
4. synthetic N-best acceptor와 compose
5. shortest path
6. output string roundtrip
7. 공백 처리 smoke
8. epsilon insertion/deletion이 필요한 길이 차이 correction smoke

Python version:

- P2에서 실제 사용 Python version을 report에 기록한다.
- 가능하면 Python 3.11 또는 3.12 기준으로 먼저 검증한다.
- Pynini wheel/conda 설치 제약이 확인되면 `requires-python` 상한 또는 environment 문서에 반영한다.

### 3.6 P5: optional identity bypass fallback 명시

현재 WBS는 optional identity bypass test를 포함한다. 여기에 fallback 정책을 추가해야 한다.

권장 완료 기준:

```text
- optional rule에서 일반 identity path가 keep_cost를 0 cost로 우회하지 못함
- cdrewrite 구현이 이 테스트를 통과하지 못하면 phrase trie 기반 leftmost-longest rule engine으로 전환함
```

MVP에서는 일반 rewrite의 표현력보다 예측 가능한 phrase-level behavior가 더 중요하다.

## 4. 반영 우선순위

다음 실제 문서/코드 수정 순서는 아래가 적절하다.

1. `docs/wbs.md`에 P3.5 추가
2. `docs/wbs.md` P9 manifest 필드 확장
3. `docs/wbs.md` P8 scope에서 `top1+rules` 비교 제거, dep를 `P3.5, P7`로 조정
4. `scripts/archive_project_snapshot.py`에 `data` 포함 및 테스트 보강
5. `docs/wbs.md` P2 smoke 완료 기준 강화
6. `docs/wbs.md` P5 optional fallback 완료 기준 추가
7. 필요 시 `docs/ops/evaluation-calibration-design.md`도 같은 manifest/targetability 정책으로 동기화

## 5. 최종 판단

리뷰는 기술적으로 유효하다.

다만 P8은 reviewer가 제시한 안 A가 더 적절하다. P8은 correction engine을 요구하지 않는 가벼운
targetability probe로 유지하고, 실제 `top1+rules` vs `N-best+rules` 비교는 P10/P11로 미룬다.

이 수정이 들어가면 다음 작업 순서는 다음이 된다.

```text
P2 FST Backend Feasibility
-> P3 Core Contracts
-> P3.5 Rule Source Audit / Seed Rule Review
-> P4/P5/P6 correction core
-> P7 HF N-best extraction
-> P8 pure targetability probe
-> P9/P10/P11 evaluation and calibration
```
