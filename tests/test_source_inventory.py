from pathlib import Path

from whisper_wfst.source_inventory import (
    assign_split,
    inventory_audio_text_sources,
    render_audio_text_inventory_report,
)


def test_inventory_matches_label_to_batch_audio_before_flat_audio(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations"
    debug_input = tmp_path / "debug" / "input"
    shared_input = tmp_path / "input"
    label_dir = annotations / "AIG_20250704"
    label_dir.mkdir(parents=True)
    label = label_dir / "sample_l.txt"
    label.write_text(
        "1\n" + "가" * 50 + "\n2\n" + "나" * 50 + "\n3\n" + "다" * 50,
        encoding="utf-8",
    )
    batch_audio = debug_input / "AIG_20250704" / "sample_l.wav"
    batch_audio.parent.mkdir(parents=True)
    batch_audio.write_bytes(b"not-a-real-wav")
    flat_audio = shared_input / "sample_l.wav"
    flat_audio.parent.mkdir(parents=True)
    flat_audio.write_bytes(b"not-a-real-wav")

    inventory = inventory_audio_text_sources(
        annotations_root=annotations,
        audio_roots=[debug_input, shared_input],
    )

    assert len(inventory.records) == 1
    record = inventory.records[0]
    assert record.source_stem == "sample_l"
    assert record.batch == "AIG_20250704"
    assert record.selected_audio_path == str(batch_audio)
    assert record.audio_candidate_count == 2
    assert record.exclusion_reasons == []


def test_inventory_records_missing_audio_and_short_label(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations"
    label_dir = annotations / "AIG_20250704"
    label_dir.mkdir(parents=True)
    (label_dir / "short_l.txt").write_text("1\n안녕\n2\n", encoding="utf-8")

    inventory = inventory_audio_text_sources(
        annotations_root=annotations,
        audio_roots=[tmp_path / "missing-input"],
    )

    record = inventory.records[0]
    assert record.selected_audio_path is None
    assert "missing_audio" in record.exclusion_reasons
    assert "too_short_label" in record.exclusion_reasons


def test_assign_split_is_deterministic() -> None:
    assert assign_split("sample_l") == assign_split("sample_l")
    assert assign_split("other_l") in {"rule_mining", "dev_review", "eval_holdout"}


def test_report_contains_counts_without_raw_text(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations"
    audio_root = tmp_path / "input"
    label_dir = annotations / "AIG_20250704"
    label_dir.mkdir(parents=True)
    (label_dir / "sample_l.txt").write_text(
        "1\n" + "나" * 50 + "\n2\n" + "다" * 50 + "\n3\n" + "라" * 50,
        encoding="utf-8",
    )
    audio = audio_root / "sample_l.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"not-a-real-wav")

    inventory = inventory_audio_text_sources(
        annotations_root=annotations,
        audio_roots=[audio_root],
    )

    report = render_audio_text_inventory_report(inventory)

    assert "Input labels: 1" in report
    assert "Matched records: 1" in report
    assert "sample_l.wav" not in report
    assert "나" * 10 not in report
