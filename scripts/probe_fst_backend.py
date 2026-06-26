from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.fst_backend import probe_pynini_backend, render_markdown_report

DEFAULT_OUTPUT = Path("docs/reports/probes/fst_backend_feasibility.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Pynini/OpenFST backend feasibility.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Markdown report output path.",
    )
    args = parser.parse_args(argv)

    result = probe_pynini_backend()
    report = render_markdown_report(result)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
