"""Helpers for repairing mojibake and normalizing text payloads."""

from __future__ import annotations

from typing import Any

MOJIBAKE_MARKERS = ("Ã", "Â", "â")


def fix_mojibake(text: Any) -> Any:
    """Repair common UTF-8-as-Latin1 mojibake without touching non-text values."""
    if not isinstance(text, str):
        return text

    cleaned = text.replace("\ufeff", "").replace("\u00ad", "")
    if not any(marker in cleaned for marker in MOJIBAKE_MARKERS):
        return cleaned

    try:
        return cleaned.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return cleaned


def repair_text_payload(value: Any) -> Any:
    """Recursively repair mojibake inside dict/list payloads."""
    if isinstance(value, dict):
        return {key: repair_text_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [repair_text_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(repair_text_payload(item) for item in value)
    return fix_mojibake(value)
