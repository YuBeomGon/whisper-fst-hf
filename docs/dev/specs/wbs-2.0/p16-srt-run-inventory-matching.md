# P16 SRT Run Inventory / Matching Spec

Date: 2026-06-26

Branch: `wbs/v2/P16-srt-run-inventory-matching`

## Goal

`shared/debug/output/**/*_l.srt` 전체를 inventory하고 P14/P15 label source와 file stem 기준으로 매칭한다.

P16은 SRT 원문을 commit하지 않는다. 각 SRT의 block count, timestamp range, run metadata, label match 여부만
저장한다.

## Inputs

```text
/data/MyProject/stt/aig/stt-engine/shared/debug/output/**/*_l.srt
/data/MyProject/stt/aig/stt-engine/shared/annotations/*/*_l.txt
```

## Matching Policy

```text
source_stem = Path(srt).stem
channel = trailing "_l"
label match = source_stem exists in parsed label source inventory
```

run metadata:

```text
debug/output/<run_id>/<variant>/<source_stem>.srt
```

If a path has deeper nesting, all path components between `run_id` and filename are joined as `variant`.

## Outputs

Committed:

```text
src/whisper_wfst/srt_inventory.py
scripts/inventory_srt_runs.py
tests/test_srt_inventory.py
docs/reports/audits/srt_run_inventory.md
docs/reviews/code/2026-06-26-p16-srt-run-inventory-matching-review.md
```

Ignored/local:

```text
outputs/wbs-2.0/srt_inventory/srt_run_inventory.json
```

## Acceptance Criteria

- all `_l.srt` files under debug output can be cataloged.
- malformed SRT files are reported instead of crashing the inventory.
- label matching is source-stem based and deterministic.
- report includes run coverage counts but no transcript text.
- `uv run --group dev pytest -q` passes.
- `uv run --group dev ruff check .` passes.
