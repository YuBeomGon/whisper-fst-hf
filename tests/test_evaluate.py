from pathlib import Path

from whisper_wfst.evaluate import (
    evaluate_predictions,
    load_evaluation_manifest,
    load_prediction_rows,
    render_evaluation_report,
)


def test_evaluate_predictions_computes_core_metrics() -> None:
    manifest = load_evaluation_manifest(Path("tests/fixtures/evaluation_manifest.json"))
    predictions = load_prediction_rows(Path("tests/fixtures/evaluation_predictions.json"))

    result = evaluate_predictions(manifest, predictions)

    assert result.segment_count == 2
    assert result.top1_cer > result.corrected_cer
    assert result.top1_wer > result.corrected_wer
    assert result.cer == result.corrected_cer == 0.0
    assert result.wer == result.corrected_wer == 0.0
    assert result.domain_term_accuracy == 1.0
    assert result.correction_precision == 1.0
    assert result.correction_recall == 1.0
    assert result.overcorrection_rate == 0.0
    assert result.free_talk_correction_rate == 0.0
    assert result.free_talk_overcorrection_rate == 0.0
    assert result.nbest_oracle_cer == 0.0
    assert result.latency_p50_ms == "not_applicable"


def test_evaluation_report_contains_abcd_comparison_and_free_talk_metrics() -> None:
    manifest = load_evaluation_manifest(Path("tests/fixtures/evaluation_manifest.json"))
    predictions = load_prediction_rows(Path("tests/fixtures/evaluation_predictions.json"))
    result = evaluate_predictions(manifest, predictions)

    report = render_evaluation_report(result)

    assert "A: top1 baseline" in report
    assert "B: top1 + correction" in report
    assert "C: N-best oracle" in report
    assert "D: N-best + correction" in report
    assert "free-talk correction rate" in report
    assert "not_applicable" in report
