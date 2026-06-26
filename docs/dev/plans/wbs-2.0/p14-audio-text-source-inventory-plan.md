# P14 Audio/Text Source Inventory Implementation Plan

## Goal

Implement deterministic `_l` label/audio inventory and split manifest generation for WBS 2.0.

## Tasks

1. Add failing tests for source stem extraction, duplicate audio selection, split determinism, and report rendering.
2. Implement `src/whisper_wfst/source_inventory.py`.
3. Add CLI `scripts/inventory_audio_text_sources.py`.
4. Generate `docs/reports/audits/audio_text_source_inventory.md` from local data.
5. Add P14 review document.
6. Update `docs/status.md`, `docs/CHANGELOG.md`, and WBS 2.0 phase status.
7. Run `pytest`, `ruff`, and `git diff --check`.
8. Commit, merge to `main`, and push.

## Notes

- Do not commit full source inventory JSON because it contains local raw data paths.
- Do not read SRT runs in P14.
- Audio duration is best-effort with Python `wave`; unreadable duration is recorded as null.
