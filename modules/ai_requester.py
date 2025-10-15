"""Lightweight heuristics that simulate AI-driven structuring."""
from __future__ import annotations

import hashlib
import textwrap
from typing import Dict, List

_KEYWORD_TO_TAG = {
    "운세": "fortune",
    "명리": "saju",
    "사주": "saju",
    "재물": "wealth",
    "건강": "health",
    "관계": "relationship",
    "career": "career",
    "love": "relationship",
    "success": "success",
}


def _extract_tags(text: str) -> List[str]:
    lowered = text.lower()
    tags = {"analysis"}
    for keyword, tag in _KEYWORD_TO_TAG.items():
        if keyword in lowered:
            tags.add(tag)
    if len(text) > 80:
        tags.add("long-form")
    if text.endswith("?"):
        tags.add("question")
    return sorted(tags)


def structurize(sentence: str, mode: str) -> Dict[str, object]:
    """Return a structured representation for a sentence.

    This function mimics an AI call while staying fully offline for development.
    """

    summary = textwrap.shorten(sentence, width=120, placeholder="...")
    tags = _extract_tags(sentence)
    digest = hashlib.sha1(sentence.encode("utf-8")).hexdigest()

    return {
        "mode": mode,
        "original": sentence,
        "summary": summary,
        "tags": tags,
        "confidence": round(min(0.99, 0.5 + len(tags) * 0.05), 2),
        "hash": digest,
    }
