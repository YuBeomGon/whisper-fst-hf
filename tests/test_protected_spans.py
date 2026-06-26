from whisper_wfst.protect import (
    ExternalSpan,
    is_index_protected,
    protect_text,
    restore_text,
)


def test_protect_text_detects_structured_sensitive_spans() -> None:
    text = (
        "연락처 010-1234-5678 주민번호 900101-1234567 "
        "금액 12,300원 날짜 2026-06-26 URL https://example.com 코드 ABC1234"
    )

    protected = protect_text(text)
    labels = {span.label for span in protected.spans}

    assert {"phone", "resident_id", "money", "date", "url", "code"} <= labels
    assert "010-1234-5678" not in protected.text
    assert "https://example.com" not in protected.text
    assert restore_text(protected.text, protected) == text


def test_protect_text_handles_external_name_span_without_auto_name_detection() -> None:
    text = "상담원 김민수입니다"

    without_external = protect_text(text)
    with_external = protect_text(text, external_spans=[ExternalSpan(4, 7, "name")])

    assert without_external.text == text
    assert with_external.text != text
    assert with_external.spans[0].label == "name"
    assert restore_text(with_external.text, with_external) == text


def test_long_digit_sequences_are_protected() -> None:
    text = "계좌 12345678901234로 입금"

    protected = protect_text(text)

    assert protected.spans[0].label == "long_number"
    assert "12345678901234" not in protected.text
    assert restore_text(protected.text, protected) == text


def test_overlapping_spans_are_merged_and_indexes_are_protected() -> None:
    text = "담당자 김민수 연락처 010-1234-5678"
    protected = protect_text(text, external_spans=[ExternalSpan(4, 7, "name")])

    assert is_index_protected(5, protected) is True
    assert is_index_protected(10, protected) is False
    assert restore_text(protected.text, protected) == text
