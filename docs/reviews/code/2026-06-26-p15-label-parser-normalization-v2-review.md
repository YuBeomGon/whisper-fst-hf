# P15 Label Parser / Normalization v2 Review

Date: 2026-06-26

Branch: `wbs/v2/P15-label-parser-normalization-v2`

## Scope Reviewed

- `src/whisper_wfst/label_parser.py`
- `scripts/audit_label_formats.py`
- `tests/test_label_parser.py`
- `data/label_parser_cases.sample.jsonl`
- `docs/reports/audits/label_format_audit.md`

## Findings

No blocking findings.

## Notes

- Parser keeps only normalized comparison text and aggregate audit metadata in committed artifacts.
- Square tags are removed from comparison text.
- Protected personal tag patterns remove adjacent angle spans.
- Angle correction markup keeps the right-side surface.
- Actual label audit parsed 47 `_l.txt` files and reported no-index fallback, index-not-first, script imbalance, and too-short counts.

## Verification

- `uv run --group dev pytest tests/test_label_parser.py -q`
- `uv run scripts/audit_label_formats.py`
