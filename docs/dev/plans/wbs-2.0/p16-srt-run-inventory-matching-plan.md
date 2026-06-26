# P16 SRT Run Inventory / Matching Implementation Plan

## Goal

Implement SRT inventory and label matching for all `_l.srt` runs.

## Tasks

1. Add failing tests for SRT timestamp parsing, run metadata extraction, malformed SRT handling, and label matching.
2. Implement `src/whisper_wfst/srt_inventory.py`.
3. Add CLI `scripts/inventory_srt_runs.py`.
4. Generate `docs/reports/audits/srt_run_inventory.md`.
5. Add P16 review document.
6. Update WBS 2.0, status, and changelog.
7. Run `pytest`, `ruff`, and `git diff --check`.
8. Commit, merge to `main`, and push.
