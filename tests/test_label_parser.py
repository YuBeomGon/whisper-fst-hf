from pathlib import Path

from whisper_wfst.label_parser import (
    audit_label_files,
    normalize_label_text,
    parse_label_text,
    render_label_format_audit_report,
)


def test_parse_label_text_builds_index_blocks_with_time_ranges() -> None:
    doc = parse_label_text("1\n안녕하세요 [NAME]\n2\n보험료 안내입니다\n", source_stem="a_l")

    assert len(doc.blocks) == 2
    assert doc.blocks[0].index == 1
    assert doc.blocks[0].start_sec == 0
    assert doc.blocks[0].end_sec == 30
    assert doc.blocks[0].normalized_text == "안녕하세요"
    assert doc.blocks[1].normalized_text == "보험료 안내입니다"


def test_parse_label_text_treats_unexpected_numeric_line_as_body_text() -> None:
    doc = parse_label_text("1\n첫 문장\n5570\n이어지는 문장\n2\n다음 문장\n", source_stem="a_l")

    assert len(doc.blocks) == 2
    assert "5570" in doc.blocks[0].normalized_text
    assert doc.blocks[1].normalized_text == "다음 문장"


def test_parse_label_text_uses_whole_file_fallback_without_index() -> None:
    doc = parse_label_text("안녕하세요\n보험 안내입니다\n", source_stem="a_l")

    assert doc.format_flags == ["no_index_fallback"]
    assert len(doc.blocks) == 1
    assert doc.blocks[0].index is None
    assert doc.blocks[0].normalized_text == "안녕하세요 보험 안내입니다"


def test_normalize_label_text_removes_square_tags_and_protected_angle_name() -> None:
    normalized = normalize_label_text("<홍길동> [NAME] 회원님 [INAUDIBLE] 연락처 [CONTACT]")

    assert "홍길동" not in normalized
    assert "NAME" not in normalized
    assert "INAUDIBLE" not in normalized
    assert "CONTACT" not in normalized
    assert normalized == "회원님 연락처"


def test_normalize_label_text_keeps_right_side_of_angle_correction_markup() -> None:
    normalized = normalize_label_text("치아 <보혐>/<보험> 안내와 <삭제대상> 문구")

    assert normalized == "치아 보험 안내와 문구"


def test_audit_label_files_reports_format_counts_without_raw_text(tmp_path: Path) -> None:
    label_dir = tmp_path / "AIG"
    label_dir.mkdir()
    (label_dir / "normal_l.txt").write_text("1\n" + "가" * 130 + "\n2\n본문", encoding="utf-8")
    (label_dir / "short_l.txt").write_text("1\n짧음\n", encoding="utf-8")

    audit = audit_label_files(tmp_path)
    report = render_label_format_audit_report(audit)

    assert audit.input_label_count == 2
    assert "too_short_label" in audit.exclusion_counts
    assert "Input labels: 2" in report
    assert "가" * 10 not in report
