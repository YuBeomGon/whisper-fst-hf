# P15 Label Parser / Normalization v2 Implementation Plan

## Goal

Implement label parser v2 and generate an aggregate audit report over the real `_l.txt` labels.

## Tasks

1. Add failing parser tests for index blocks, numeric body lines, tag removal, angle correction markup, and fallback.
2. Implement `src/whisper_wfst/label_parser.py`.
3. Add CLI `scripts/audit_label_formats.py`.
4. Add safe synthetic sample cases under `data/label_parser_cases.sample.jsonl`.
5. Generate `docs/reports/audits/label_format_audit.md`.
6. Add P15 review document.
7. Update WBS 2.0, status, and changelog.
8. Run `pytest`, `ruff`, and `git diff --check`.
9. Commit, merge to `main`, and push.
