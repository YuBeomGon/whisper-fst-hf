from __future__ import annotations

import argparse
from pathlib import Path

from whisper_wfst.pair_mining import (
    mine_pair_candidates,
    render_pair_mining_report,
    write_pair_candidates_csv,
    write_pair_candidates_jsonl,
)

DEFAULT_SRT_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/debug/output")
DEFAULT_ANNOTATIONS_ROOT = Path("/data/MyProject/stt/aig/stt-engine/shared/annotations")
DEFAULT_OUTPUT_DIR = Path("outputs/pair_mining")
DEFAULT_REPORT = Path("docs/reports/audits/misrecognition_pair_mining.md")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine misrecognition pair candidates.")
    parser.add_argument("--srt-root", type=Path, default=DEFAULT_SRT_ROOT)
    parser.add_argument("--annotations-root", type=Path, default=DEFAULT_ANNOTATIONS_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    result = mine_pair_candidates(args.srt_root, args.annotations_root)
    write_pair_candidates_csv(result.candidates, args.output_dir / "pair_candidates.csv")
    write_pair_candidates_jsonl(result.candidates, args.output_dir / "pair_candidates.jsonl")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_pair_mining_report(
            candidate_count=len(result.candidates),
            occurrence_count=result.occurrence_count,
            srt_files_scanned=result.srt_files_scanned,
            invalid_srt_count=result.invalid_srt_count,
            label_count=result.label_count,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
