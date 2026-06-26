from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from whisper_wfst.artifact_io import read_nbest_artifact
from whisper_wfst.evaluate import (
    evaluate_predictions,
    load_evaluation_manifest,
    load_prediction_rows,
    render_evaluation_report,
)
from whisper_wfst.rule_io import read_correction_rules_csv
from whisper_wfst.safety import (
    CorrectionSafetyConfig,
    SegmentCorrectionContext,
    apply_correction_safely,
)
from whisper_wfst.targetability import compute_targetability, render_targetability_report


@dataclass(frozen=True)
class OfflinePipelinePaths:
    nbest_artifact: Path
    targetability_manifest: Path
    rules: Path
    evaluation_manifest: Path
    evaluation_predictions: Path
    output_dir: Path
    report_path: Path
    manifest_path: Path


@dataclass(frozen=True)
class OfflinePipelineResult:
    trace_path: Path
    evaluation_report_path: Path
    report_path: Path
    manifest_path: Path
    targetability_risk_flag: str
    checksums: dict[str, str]
    report_text: str


def run_offline_pipeline(paths: OfflinePipelinePaths) -> OfflinePipelineResult:
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    artifact = read_nbest_artifact(paths.nbest_artifact)
    target_manifest = json.loads(paths.targetability_manifest.read_text(encoding="utf-8"))
    rules = read_correction_rules_csv(paths.rules)

    targetability = compute_targetability(
        artifacts=[artifact],
        references=target_manifest["references"],
        domain_terms=target_manifest["domain_terms"],
        seed_rules=rules,
    )
    trace = apply_correction_safely(
        artifact,
        rules,
        CorrectionSafetyConfig(domain_gate_enabled=True, margin=1.0),
        SegmentCorrectionContext(
            segment_id=artifact.segment_id,
            domain_allowed=True,
            is_free_talk=False,
        ),
    )
    trace_path = paths.output_dir / "correction_trace.json"
    trace_path.write_text(
        json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    evaluation = evaluate_predictions(
        load_evaluation_manifest(paths.evaluation_manifest),
        load_prediction_rows(paths.evaluation_predictions),
    )
    evaluation_report = render_evaluation_report(evaluation)
    evaluation_report_path = paths.output_dir / "evaluation_report.md"
    evaluation_report_path.write_text(evaluation_report, encoding="utf-8")

    checksums = {
        str(path): _sha256(path)
        for path in [
            paths.nbest_artifact,
            paths.targetability_manifest,
            paths.rules,
            paths.evaluation_manifest,
            paths.evaluation_predictions,
            trace_path,
            evaluation_report_path,
        ]
    }
    report_text = _render_offline_report(
        targetability_report=render_targetability_report(targetability),
        evaluation_report=evaluation_report,
        risk_flag=targetability.p10_risk_flag,
        checksums=checksums,
    )
    paths.report_path.parent.mkdir(parents=True, exist_ok=True)
    paths.report_path.write_text(report_text, encoding="utf-8")

    manifest = {
        "mode": "synthetic_fixture_offline_mvp",
        "targetability_risk_flag": targetability.p10_risk_flag,
        "paths": {key: key for key in checksums},
        "checksums": checksums,
    }
    paths.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    paths.manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    checksums[str(paths.report_path)] = _sha256(paths.report_path)
    checksums[str(paths.manifest_path)] = _sha256(paths.manifest_path)
    return OfflinePipelineResult(
        trace_path=trace_path,
        evaluation_report_path=evaluation_report_path,
        report_path=paths.report_path,
        manifest_path=paths.manifest_path,
        targetability_risk_flag=targetability.p10_risk_flag,
        checksums=checksums,
        report_text=report_text,
    )


def _render_offline_report(
    *,
    targetability_report: str,
    evaluation_report: str,
    risk_flag: str,
    checksums: dict[str, str],
) -> str:
    checksum_lines = [f"- `{path}`: `{checksum}`" for path, checksum in checksums.items()]
    return "\n".join(
        [
            "# Offline MVP Run",
            "",
            "Mode: synthetic fixture offline MVP.",
            "",
            f"P8 targetability risk flag: {risk_flag}",
            "",
            "No production-quality claim is made from this run.",
            "",
            "## Targetability",
            "",
            targetability_report,
            "## Evaluation",
            "",
            evaluation_report,
            "## Checksums",
            "",
            *checksum_lines,
            "",
        ]
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


__all__ = ["OfflinePipelinePaths", "OfflinePipelineResult", "run_offline_pipeline"]
