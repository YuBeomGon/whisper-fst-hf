from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def normalized_key(text: str) -> str:
    return normalize_text(text)


__all__ = ["normalize_text", "normalized_key"]
