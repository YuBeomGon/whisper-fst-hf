from pathlib import Path

from whisper_wfst.srt_inventory import (
    inventory_srt_runs,
    parse_srt_file,
    render_srt_run_inventory_report,
)


def test_parse_srt_file_extracts_block_count_and_time_range(tmp_path: Path) -> None:
    srt = tmp_path / "sample_l.srt"
    srt.write_text(
        "1\n"
        "00:00:01,000 --> 00:00:03,500\n"
        "안녕하세요\n\n"
        "2\n"
        "00:00:04,000 --> 00:00:05,000\n"
        "보험 안내입니다\n",
        encoding="utf-8",
    )

    meta = parse_srt_file(srt)

    assert meta.block_count == 2
    assert meta.first_start_sec == 1.0
    assert meta.last_end_sec == 5.0
    assert meta.is_valid


def test_parse_srt_file_marks_malformed_file(tmp_path: Path) -> None:
    srt = tmp_path / "bad_l.srt"
    srt.write_text("not an srt", encoding="utf-8")

    meta = parse_srt_file(srt)

    assert not meta.is_valid
    assert meta.block_count == 0


def test_inventory_srt_runs_extracts_run_variant_and_matches_labels(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations" / "AIG"
    annotations.mkdir(parents=True)
    (annotations / "sample_l.txt").write_text("1\n" + "가" * 130, encoding="utf-8")
    srt_dir = tmp_path / "output" / "run_a" / "candidate"
    srt_dir.mkdir(parents=True)
    (srt_dir / "sample_l.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n가\n", encoding="utf-8"
    )
    (srt_dir / "extra_l.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n나\n", encoding="utf-8"
    )

    inventory = inventory_srt_runs(
        srt_root=tmp_path / "output",
        annotations_root=tmp_path / "annotations",
    )

    assert inventory.total_srt_count == 2
    assert inventory.matched_srt_count == 1
    sample = [record for record in inventory.records if record.source_stem == "sample_l"][0]
    assert sample.run_id == "run_a"
    assert sample.variant == "candidate"
    assert sample.label_matched


def test_report_contains_run_coverage_without_transcript_text(tmp_path: Path) -> None:
    annotations = tmp_path / "annotations" / "AIG"
    annotations.mkdir(parents=True)
    (annotations / "sample_l.txt").write_text("1\n" + "가" * 130, encoding="utf-8")
    srt_dir = tmp_path / "output" / "run_a" / "baseline"
    srt_dir.mkdir(parents=True)
    (srt_dir / "sample_l.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n민감한본문\n", encoding="utf-8"
    )

    inventory = inventory_srt_runs(
        srt_root=tmp_path / "output",
        annotations_root=tmp_path / "annotations",
    )
    report = render_srt_run_inventory_report(inventory)

    assert "Input SRT files: 1" in report
    assert "run_a" in report
    assert "민감한본문" not in report
