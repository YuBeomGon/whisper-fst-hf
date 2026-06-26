from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.artifact_io import read_nbest_artifact
from whisper_wfst.rule_io import read_correction_rules_csv
from whisper_wfst.targetability import compute_targetability, render_targetability_report

DEFAULT_ARTIFACT = Path("tests/fixtures/targetability_artifact.json")
DEFAULT_MANIFEST = Path("tests/fixtures/targetability_manifest.json")
DEFAULT_RULES = Path("tests/fixtures/correction_rules.csv")
DEFAULT_OUTPUT = Path("docs/reports/probes/nbest_targetability_probe.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe HF N-best targetability.")
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = compute_targetability(
        artifacts=[read_nbest_artifact(args.artifact)],
        references=manifest["references"],
        domain_terms=manifest["domain_terms"],
        seed_rules=read_correction_rules_csv(args.rules),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_targetability_report(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
