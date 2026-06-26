from pathlib import Path

from whisper_wfst.offline_pipeline import OfflinePipelinePaths, run_offline_pipeline


def test_offline_pipeline_writes_outputs_and_manifest(tmp_path: Path) -> None:
    paths = OfflinePipelinePaths(
        nbest_artifact=Path("tests/fixtures/targetability_artifact.json"),
        targetability_manifest=Path("tests/fixtures/targetability_manifest.json"),
        rules=Path("tests/fixtures/correction_rules.csv"),
        evaluation_manifest=Path("tests/fixtures/evaluation_manifest.json"),
        evaluation_predictions=Path("tests/fixtures/evaluation_predictions.json"),
        output_dir=tmp_path / "outputs",
        report_path=tmp_path / "offline_mvp_run.md",
        manifest_path=tmp_path / "offline_mvp_manifest.json",
    )

    result = run_offline_pipeline(paths)

    assert result.trace_path.exists()
    assert result.evaluation_report_path.exists()
    assert result.manifest_path.exists()
    assert result.targetability_risk_flag == "ok"
    assert len(result.checksums) >= 3
    assert "No production-quality claim" in result.report_text
    assert "P8 targetability risk flag: ok" in result.report_text
