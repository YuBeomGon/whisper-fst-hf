# P15 Label Parser / Normalization v2 Spec

Date: 2026-06-26

Branch: `wbs/v2/P15-label-parser-normalization-v2`

## Goal

전사자 `_l.txt` label을 WBS 2.0 pair mining에 사용할 reference text block으로 변환한다.

P15는 label 원문을 commit하지 않는다. parser는 local raw label을 읽어 normalized reference view와 audit
metadata를 만든다.

## Behavior

- 30초 index block을 파싱한다.
- index가 첫 줄이 아니어도 연속 numeric sequence를 찾는다.
- 숫자-only 본문이 index sequence와 맞지 않으면 text로 취급한다.
- index가 없으면 whole-file fallback block을 만든다.
- 너무 짧은 label은 `too_short_label`로 제외 표시한다.
- square tag는 comparison text에서 제거한다.
- `[NAME]`, `[CONTACT]`, `[ADDR]`와 인접한 angle/person span은 protected source로 표시한다.
- `<wrong>/<right>`, `<wrong> / <right>`, `<wrong>-><right>`, `<wrong> => <right>`는 오른쪽을 정인식으로 남긴다.
- standalone `<...>`는 comparison text에서 제거한다.
- `[SCRIPT_START]` / `[SCRIPT_END]` imbalance는 flag로 남긴다.

## Outputs

Committed:

```text
src/whisper_wfst/label_parser.py
scripts/audit_label_formats.py
tests/test_label_parser.py
data/label_parser_cases.sample.jsonl
docs/reports/audits/label_format_audit.md
docs/reviews/code/2026-06-26-p15-label-parser-normalization-v2-review.md
```

Ignored/local:

```text
outputs/wbs-2.0/label_parser/label_format_audit.json
```

## Acceptance Criteria

- parser handles normal indexed labels.
- parser handles indexless fallback.
- parser ignores numeric-only body lines that are not expected index values.
- square tags are removed from normalized text.
- angle correction markup keeps the right-side text.
- protected personal spans do not remain in normalized text.
- label format audit reports all 47 `_l.txt` labels without raw transcript text.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
