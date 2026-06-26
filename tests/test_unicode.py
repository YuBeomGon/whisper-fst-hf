from whisper_wfst.normalize import normalize_text, normalized_key


def test_normalize_text_uses_nfc_for_hangul() -> None:
    nfc = "가"
    nfd = "\u1100\u1161"

    assert normalize_text(nfd) == nfc
    assert normalized_key(nfc) == normalized_key(nfd)


def test_normalized_key_preserves_meaningful_spacing() -> None:
    assert normalized_key("보험 가입") != normalized_key("보험가입")
