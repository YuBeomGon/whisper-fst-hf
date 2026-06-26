from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalSpan:
    start: int
    end: int
    label: str


@dataclass(frozen=True)
class ProtectedSpan:
    start: int
    end: int
    label: str
    text: str
    placeholder: str


@dataclass(frozen=True)
class ProtectedText:
    original_text: str
    text: str
    spans: list[ProtectedSpan]


_STRUCTURED_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("url", re.compile(r"https?://[^\s]+")),
    ("resident_id", re.compile(r"\b\d{6}-\d{7}\b")),
    ("phone", re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b")),
    ("money", re.compile(r"\b\d{1,3}(?:,\d{3})+원\b|\b\d+원\b")),
    ("date", re.compile(r"\b\d{4}[.-]\d{2}[.-]\d{2}\b")),
    ("long_number", re.compile(r"\d{10,}")),
    ("code", re.compile(r"\b[A-Z]{2,}\d{3,}\b")),
)


def protect_text(
    text: str,
    *,
    external_spans: list[ExternalSpan] | None = None,
) -> ProtectedText:
    raw_spans: list[tuple[int, int, str]] = []
    for label, pattern in _STRUCTURED_PATTERNS:
        for match in pattern.finditer(text):
            raw_spans.append((match.start(), match.end(), label))
    for span in external_spans or []:
        _validate_external_span(text, span)
        raw_spans.append((span.start, span.end, span.label))

    merged = _merge_spans(raw_spans)
    protected_spans: list[ProtectedSpan] = []
    output_parts: list[str] = []
    cursor = 0
    for index, (start, end, label) in enumerate(merged):
        placeholder = f"__PROT_{index:04d}__"
        output_parts.append(text[cursor:start])
        output_parts.append(placeholder)
        protected_spans.append(
            ProtectedSpan(
                start=start,
                end=end,
                label=label,
                text=text[start:end],
                placeholder=placeholder,
            )
        )
        cursor = end
    output_parts.append(text[cursor:])
    return ProtectedText(
        original_text=text,
        text="".join(output_parts),
        spans=protected_spans,
    )


def restore_text(text: str, protected_text: ProtectedText) -> str:
    restored = text
    for span in protected_text.spans:
        restored = restored.replace(span.placeholder, span.text)
    return restored


def is_index_protected(index: int, protected_text: ProtectedText) -> bool:
    return any(span.start <= index < span.end for span in protected_text.spans)


def _validate_external_span(text: str, span: ExternalSpan) -> None:
    if span.start < 0 or span.end < span.start or span.end > len(text):
        raise ValueError("external span is outside text bounds")
    if not span.label:
        raise ValueError("external span label must be non-empty")


def _merge_spans(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    if not spans:
        return []
    ordered = sorted(spans, key=lambda span: (span[0], span[1]))
    merged: list[tuple[int, int, str]] = []
    for start, end, label in ordered:
        if not merged or start > merged[-1][1]:
            merged.append((start, end, label))
            continue
        prev_start, prev_end, prev_label = merged[-1]
        merged[-1] = (prev_start, max(prev_end, end), prev_label)
    return merged


__all__ = [
    "ExternalSpan",
    "ProtectedSpan",
    "ProtectedText",
    "is_index_protected",
    "protect_text",
    "restore_text",
]
