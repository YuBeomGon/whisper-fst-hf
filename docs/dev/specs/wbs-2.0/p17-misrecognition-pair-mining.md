# P17 Misrecognition Pair Mining Spec

Date: 2026-06-26

Branch: `wbs/v2/P17-misrecognition-pair-mining`

## Goal

P15 normalized label reference와 P16 valid SRT hypothesis를 비교해 `wrong -> right` pair 후보를 생성한다.

P17은 실제 후보 전체를 local ignored artifact로만 저장한다. repository에는 schema/sample과 aggregate report만
commit한다.

## Mining Policy

- label block은 P15 parser의 30초 approximate time range를 사용한다.
- SRT block midpoint가 label block range와 tolerance 안에 있으면 비교한다.
- diff span은 char alignment 후 좌우 whitespace boundary로 확장한다.
- too-short, too-long, digit-only, empty-side pair는 reject한다.
- support는 run/file/batch/variant를 분리한다.
- 같은 파일을 여러 sweep이 반복한 것은 file support 1개로 계산한다.

## Outputs

Committed:

```text
src/whisper_wfst/pair_mining.py
scripts/mine_misrecognition_pairs.py
tests/test_pair_mining.py
data/pair_candidates.sample.csv
docs/reports/audits/misrecognition_pair_mining.md
docs/reviews/code/2026-06-26-p17-misrecognition-pair-mining-review.md
```

Ignored/local:

```text
outputs/pair_mining/pair_candidates.csv
outputs/pair_mining/pair_candidates.jsonl
```

## Acceptance Criteria

- wrong/right phrase candidates are extracted from aligned label/SRT text.
- support counts are split into run/file/batch/variant counts.
- invalid SRT and excluded labels are skipped.
- full actual candidate CSV is not committed.
- aggregate report has counts only.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
