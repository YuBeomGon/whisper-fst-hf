# P18 Pair Review / Rule Source Audit v2 Spec

Date: 2026-06-26

Branch: `wbs/v2/P18-pair-review-rule-source-audit-v2`

## Goal

P17 pair candidate artifact를 split/provenance/risk/support 기준으로 감사해 leakage-safe seed rule CSV를 만든다.

P18은 실제 candidate 표면을 repository에 커밋하지 않는다. aggregate report, schema, synthetic sample만 커밋한다.

## Review Policy

- `eval_holdout` source에만 존재하는 pair는 seed rule로 승격하지 않는다.
- `rule_mining` 또는 `dev_review` source support가 threshold 이상인 pair만 seed 후보가 될 수 있다.
- `low_alignment_confidence`, protected/PII/number-like surface, 과도하게 긴 span은 reject한다.
- 단일 파일 support 후보는 `needs_review`로 남기고 seed rule에서 제외한다.
- 충분한 support지만 일반적인 경우는 `optional` rule로 승격한다.
- 매우 높은 support/confidence 후보만 `obligatory` rule로 승격할 수 있다.
- 자동 승격은 비슷한 길이의 단일 토큰 치환으로 제한한다.
- 공백/문장부호/접사 삽입삭제/큰 길이 차이 후보는 자동 seed가 아니라 reject 또는 manual review 대상으로 둔다.
- 모든 seed rule은 `pair_id`, allowed support count, split provenance를 source field에 남긴다.

## Outputs

Committed:

```text
src/whisper_wfst/pair_review.py
scripts/audit_pair_sources.py
tests/test_pair_review.py
data/pair_review_schema.csv
data/correction_rules_seed_v2.sample.csv
docs/reports/audits/pair_rule_source_audit_v2.md
docs/reviews/code/2026-06-26-p18-pair-review-rule-source-audit-v2-review.md
```

Ignored/local:

```text
outputs/pair_mining/correction_rules_seed_v2.csv
outputs/pair_mining/pair_rule_source_audit_v2.csv
```

## Acceptance Criteria

- eval-only candidate cannot become a seed rule.
- risky or low-confidence candidate is rejected.
- support thresholds separate `needs_review` from seed rules.
- generated seed CSV conforms to the existing correction rule schema.
- committed report omits actual wrong/right surfaces.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
