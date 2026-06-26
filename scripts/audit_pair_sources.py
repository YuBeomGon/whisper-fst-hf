from __future__ import annotations

import argparse
from pathlib import Path

from whisper_wfst.pair_review import (
    audit_pair_candidates,
    derive_split_by_source,
    load_split_manifest,
    read_pair_candidates_csv,
    render_pair_rule_source_audit_report,
    write_pair_review_csv,
    write_seed_rules_csv,
)

DEFAULT_CANDIDATES = Path("outputs/pair_mining/pair_candidates.csv")
DEFAULT_SPLIT_MANIFEST = Path("outputs/wbs-2.0/source_inventory/split_manifest.json")
DEFAULT_REVIEW_CSV = Path("outputs/pair_mining/pair_rule_source_audit_v2.csv")
DEFAULT_SEED_CSV = Path("outputs/pair_mining/correction_rules_seed_v2.csv")
DEFAULT_REPORT = Path("docs/reports/audits/pair_rule_source_audit_v2.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit pair candidates for seed rules.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--split-manifest", type=Path, default=DEFAULT_SPLIT_MANIFEST)
    parser.add_argument("--review-csv", type=Path, default=DEFAULT_REVIEW_CSV)
    parser.add_argument("--seed-csv", type=Path, default=DEFAULT_SEED_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    candidates = read_pair_candidates_csv(args.candidates)
    if args.split_manifest.exists():
        split_by_source = load_split_manifest(args.split_manifest)
    else:
        split_by_source = derive_split_by_source(candidates)

    result = audit_pair_candidates(candidates, split_by_source)
    write_pair_review_csv(result, args.review_csv)
    write_seed_rules_csv(result, args.seed_csv)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_pair_rule_source_audit_report(result), encoding="utf-8")


if __name__ == "__main__":
    main()
