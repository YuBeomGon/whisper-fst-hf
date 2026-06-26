# P18 Pair Review / Rule Source Audit v2 Implementation Plan

## Goal

Audit P17 pair candidates and create a leakage-safe seed rule CSV for downstream real evaluation.

## Tasks

1. Add failing tests for eval-only rejection, risk rejection, support thresholds, seed CSV schema, and redacted report.
2. Implement `src/whisper_wfst/pair_review.py`.
3. Add CLI `scripts/audit_pair_sources.py`.
4. Add committed schema/sample CSV files.
5. Run the audit against local P17 candidate artifacts.
6. Generate aggregate report `docs/reports/audits/pair_rule_source_audit_v2.md`.
7. Add P18 review document.
8. Update WBS 2.0, status, and changelog.
9. Run `pytest`, `ruff`, and `git diff --check`.
10. Commit, merge to `main`, and push.
