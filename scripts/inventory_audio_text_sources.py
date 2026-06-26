from __future__ import annotations

import argparse
from pathlib import Path

from whisper_wfst.source_inventory import (
    inventory_audio_text_sources,
    render_audio_text_inventory_report,
    write_inventory_json,
    write_split_manifest,
)

DEFAULT_ANNOTATIONS_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/annotations")
DEFAULT_AUDIO_ROOTS = [
    Path("/data/MyProject/stt/aig/stt-engine/shared/debug/input"),
    Path("/data/MyProject/stt/aig/stt-engine/shared/input"),
]
DEFAULT_OUTPUT_DIR = Path("outputs/wbs-2.0/source_inventory")
DEFAULT_REPORT = Path("docs/reports/audits/audio_text_source_inventory.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory AIG _l audio/text sources.")
    parser.add_argument("--annotations-root", type=Path, default=DEFAULT_ANNOTATIONS_ROOT)
    parser.add_argument("--audio-root", action="append", type=Path, dest="audio_roots")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    audio_roots = args.audio_roots or DEFAULT_AUDIO_ROOTS
    inventory = inventory_audio_text_sources(args.annotations_root, audio_roots)

    write_inventory_json(inventory, args.output_dir / "source_inventory.json")
    write_split_manifest(inventory, args.output_dir / "split_manifest.json")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_audio_text_inventory_report(inventory), encoding="utf-8")


if __name__ == "__main__":
    main()
