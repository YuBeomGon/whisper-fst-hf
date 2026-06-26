from __future__ import annotations

import argparse
from pathlib import Path

from whisper_wfst.srt_inventory import (
    inventory_srt_runs,
    render_srt_run_inventory_report,
    write_srt_inventory_json,
)

DEFAULT_SRT_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/debug/output")
DEFAULT_ANNOTATIONS_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/annotations")
DEFAULT_OUTPUT = Path("outputs/wbs-2.0/srt_inventory/srt_run_inventory.json")
DEFAULT_REPORT = Path("docs/reports/audits/srt_run_inventory.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory AIG _l SRT runs.")
    parser.add_argument("--srt-root", type=Path, default=DEFAULT_SRT_ROOT)
    parser.add_argument("--annotations-root", type=Path, default=DEFAULT_ANNOTATIONS_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    inventory = inventory_srt_runs(args.srt_root, args.annotations_root)
    write_srt_inventory_json(inventory, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_srt_run_inventory_report(inventory), encoding="utf-8")


if __name__ == "__main__":
    main()
