from pathlib import Path

import pytest

from whisper_wfst.evaluate import EvaluationValidationError, load_evaluation_manifest


def test_load_evaluation_manifest_validates_required_fields() -> None:
    entries = load_evaluation_manifest(Path("tests/fixtures/evaluation_manifest.json"))

    assert entries[0].segment_id == "eval-seg-001"
    assert entries[0].channel == "l"
    assert entries[0].is_script_span is True
    assert entries[1].is_free_talk is True


def test_load_evaluation_manifest_rejects_missing_required_field(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text('[{"segment_id": "bad"}]', encoding="utf-8")

    with pytest.raises(EvaluationValidationError, match="audio_ref"):
        load_evaluation_manifest(path)
