from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from whisper_wfst.artifact_io import write_nbest_artifact
from whisper_wfst.hf_extractor import (
    HFExtractorConfig,
    HFHypothesisOutput,
    build_nbest_artifact_from_outputs,
    render_hf_nbest_smoke_report,
    summarize_nbest_artifact,
)

DEFAULT_ARTIFACT_OUTPUT = Path("outputs/hf_nbest_mock_artifact.json")
DEFAULT_REPORT_OUTPUT = Path("docs/reports/probes/hf_nbest_smoke.md")


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract HF Whisper N-best artifacts.")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mocked generation.")
    parser.add_argument("--artifact-output", type=Path, default=DEFAULT_ARTIFACT_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    args = parser.parse_args(argv)

    if not args.mock:
        parser.error("P7 CLI currently supports --mock only; real HF runtime is deferred.")

    config = HFExtractorConfig(num_beams=20, num_return_sequences=20, length_penalty=1.0)
    artifact = build_nbest_artifact_from_outputs(
        segment_id="mock-seg-001",
        model="openai/whisper-large-v3",
        config=config,
        outputs=[
            HFHypothesisOutput([1, 2], "손해보혐", -1.0),
            HFHypothesisOutput([3, 4], "손해보혐", -1.2),
            HFHypothesisOutput([5, 6], "손해보험", -1.8),
        ],
        audio_ref="mock.wav",
    )
    write_nbest_artifact(artifact, args.artifact_output)
    summary = summarize_nbest_artifact(artifact, requested_hypotheses=config.num_return_sequences)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(render_hf_nbest_smoke_report(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
