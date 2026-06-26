from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.rule_source_audit import (
    audit_rule_sources,
    load_rule_source_jsonl,
    render_rule_source_audit_report,
    write_safe_seed_csv,
)

DEFAULT_INPUT = Path("data/rule_source_candidates.sample.jsonl")
DEFAULT_SEED_OUTPUT = Path("data/correction_rules_seed.csv")
DEFAULT_REPORT_OUTPUT = Path("docs/reports/probes/rule_source_audit.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit correction rule source provenance.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--seed-output", type=Path, default=DEFAULT_SEED_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    records = load_rule_source_jsonl(args.input)
    audited = audit_rule_sources(records)

    write_safe_seed_csv(audited, args.seed_output)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(
        render_rule_source_audit_report(audited),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
