# P16 SRT Run Inventory / Matching Review

Date: 2026-06-26

Branch: `wbs/v2/P16-srt-run-inventory-matching`

## Scope Reviewed

- `src/whisper_wfst/srt_inventory.py`
- `scripts/inventory_srt_runs.py`
- `tests/test_srt_inventory.py`
- `docs/reports/audits/srt_run_inventory.md`

## Findings

No blocking findings.

## Notes

- The committed report contains run coverage and aggregate counts only.
- Full SRT inventory JSON is a local ignored artifact under `outputs/wbs-2.0/srt_inventory/`.
- Actual inventory cataloged 4,655 `_l.srt` files across 167 runs.
- 131 SRT files have no parseable timestamp and are marked invalid rather than silently accepted.

## Verification

- `uv run --group dev pytest tests/test_srt_inventory.py -q`
- `uv run scripts/inventory_srt_runs.py`
