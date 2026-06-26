# P17 Misrecognition Pair Mining Implementation Plan

## Goal

Implement local mining of `wrong -> right` candidate pairs from valid SRT and normalized labels.

## Tasks

1. Add failing tests for phrase extraction, digit rejection, support aggregation, and report rendering.
2. Implement `src/whisper_wfst/pair_mining.py`.
3. Add CLI `scripts/mine_misrecognition_pairs.py`.
4. Generate local full candidate CSV/JSONL under `outputs/pair_mining/`.
5. Add committed redacted/sample CSV schema.
6. Generate aggregate report `docs/reports/audits/misrecognition_pair_mining.md`.
7. Add P17 review document.
8. Update WBS 2.0, status, and changelog.
9. Run `pytest`, `ruff`, and `git diff --check`.
10. Commit, merge to `main`, and push.
