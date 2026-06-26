from __future__ import annotations

import argparse
from pathlib import Path

from whisper_wfst.label_parser import (
    audit_label_files,
    render_label_format_audit_report,
    write_label_format_audit_json,
)

DEFAULT_LABEL_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/annotations")
DEFAULT_OUTPUT = Path("outputs/wbs-2.0/label_parser/label_format_audit.json")
DEFAULT_REPORT = Path("docs/reports/audits/label_format_audit.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit AIG _l label parser formats.")
    parser.add_argument("--label-root", type=Path, default=DEFAULT_LABEL_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    audit = audit_label_files(args.label_root)
    write_label_format_audit_json(audit, args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_label_format_audit_report(audit), encoding="utf-8")


if __name__ == "__main__":
    main()
