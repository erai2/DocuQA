"""Utility helpers for natural-language aware document parsing.

This module consolidates text pre-processing and heuristic classification
logic so that the different parsing strategies (rule-based, ML-assisted and
hybrid) can share the same natural language friendly behaviour.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 텍스트 전처리
# ---------------------------------------------------------------------------


def normalize_text(text: str) -> str:
    """일관된 개행/공백 구조로 정리한다."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("\u3000", " ")  # 전각 공백 제거
    normalized = re.sub(r"\t+", " ", normalized)
    normalized = re.sub(r" +", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _clean_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[\-\*•]+\s*", "", line)
    return line


def split_into_paragraphs(text: str) -> List[str]:
    """빈 줄을 기준으로 자연스러운 문단을 구성한다."""

    paragraphs: List[str] = []
    for raw_block in re.split(r"(?:\n\s*\n)+", text):
        lines = [_clean_line(line) for line in raw_block.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            continue
        paragraph = " ".join(lines)
        paragraph = re.sub(r"\s{2,}", " ", paragraph).strip()
        if not paragraph:
            continue
        paragraphs.append(paragraph)

    # 너무 짧은 문단은 앞 문단과 결합하여 읽기 좋게 만든다.
    merged: List[str] = []
    for paragraph in paragraphs:
        if merged:
            prev = merged[-1]
            if len(paragraph) < 70 and not paragraph.endswith(('.', '!', '?')):
                merged[-1] = f"{prev} {paragraph}".strip()
                continue
        merged.append(paragraph)

    return merged


# ---------------------------------------------------------------------------
# 문단 구조 분석
# ---------------------------------------------------------------------------


HEADING_KEYWORDS = [
    "개요",
    "소개",
    "정의",
    "사례",
    "규칙",
    "조건",
    "요약",
    "분석",
]


def split_heading_and_body(paragraph: str) -> Tuple[Optional[str], str]:
    """문단에서 제목과 본문을 분리한다."""

    colon_match = re.match(
        r"^(?P<head>[\w가-힣一-龥\s]{2,40})\s*[:：-]\s*(?P<body>.+)$", paragraph
    )
    if colon_match:
        heading = colon_match.group("head").strip()
        body = colon_match.group("body").strip()
        if body:
            return heading, body

    # 제목만 있는 문장일 경우
    if (
        len(paragraph) <= 40
        and not re.search(r"[.!?。！？]", paragraph)
        and any(keyword in paragraph for keyword in HEADING_KEYWORDS)
    ):
        return paragraph.strip(), ""

    return None, paragraph


def is_heading_candidate(paragraph: str) -> bool:
    """제목으로 보이는 짧은 문장을 판별한다."""

    if len(paragraph) <= 35 and not re.search(r"[.!?。！？]", paragraph):
        if re.match(r"^(?:제?\d+[장절조]|[0-9]+(?:\.[0-9]+)*|[IVX]+[.)]?)", paragraph):
            return True
        if any(keyword in paragraph for keyword in HEADING_KEYWORDS):
            return True
    return False


def iter_structured_paragraphs(text: str) -> Iterable[Dict[str, Optional[str]]]:
    """문단과 해당 문단이 속한 섹션 정보를 생성한다."""

    normalized = normalize_text(text)
    paragraphs = split_into_paragraphs(normalized)

    current_section: Optional[str] = None
    for paragraph in paragraphs:
        heading, body = split_heading_and_body(paragraph)
        if heading and not body:
            current_section = heading
            continue
        if heading and body:
            current_section = heading
            yield {"section": heading, "paragraph": body}
            continue
        if is_heading_candidate(paragraph):
            current_section = paragraph
            continue

        yield {"section": current_section, "paragraph": paragraph}


# ---------------------------------------------------------------------------
# 문단 분류 로직
# ---------------------------------------------------------------------------


CASE_KEYWORDS = [
    "사례",
    "예시",
    "케이스",
    "case",
    "적용",
    "사건",
    "예로",
]

RULE_KEYWORDS = [
    "규칙",
    "조건",
    "원칙",
    "법칙",
    "기준",
    "요건",
    "해야",
    "하지 말",
    "금지",
]

CONCEPT_KEYWORDS = [
    "정의",
    "개념",
    "설명",
    "배경",
    "의미",
    "해석",
    "구성",
]

CASE_PATTERNS = [
    re.compile(r"[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]"),
    re.compile(r"예[:：]\s"),
]

RULE_PATTERNS = [
    re.compile(r"해야 한다"),
    re.compile(r"(when|if) ", re.IGNORECASE),
    re.compile(r"조건"),
]

CONCEPT_PATTERNS = [
    re.compile(r"정의"),
    re.compile(r"개념"),
]


def _score_keywords(text: str, keywords: List[str], weight: int = 1) -> int:
    score = 0
    for keyword in keywords:
        if keyword in text:
            score += weight
    return score


def _score_patterns(text: str, patterns: List[re.Pattern], weight: int = 2) -> int:
    score = 0
    for pattern in patterns:
        if pattern.search(text):
            score += weight
    return score


def classify_paragraph(paragraph: str, section: Optional[str] = None) -> str:
    """문단을 사례/규칙/개념 중 하나로 분류한다."""

    case_score = _score_keywords(paragraph, CASE_KEYWORDS, 2)
    rule_score = _score_keywords(paragraph, RULE_KEYWORDS, 2)
    concept_score = _score_keywords(paragraph, CONCEPT_KEYWORDS, 2)

    case_score += _score_patterns(paragraph, CASE_PATTERNS, 3)
    rule_score += _score_patterns(paragraph, RULE_PATTERNS, 3)
    concept_score += _score_patterns(paragraph, CONCEPT_PATTERNS, 3)

    if section:
        lowered_section = section.lower()
        case_score += _score_keywords(lowered_section, CASE_KEYWORDS, 1)
        rule_score += _score_keywords(lowered_section, RULE_KEYWORDS, 1)
        concept_score += _score_keywords(lowered_section, CONCEPT_KEYWORDS, 1)

    # 규칙 문단은 숫자 나열/명령형 표현이 많다.
    if re.search(r"\b\d+\.\s", paragraph):
        rule_score += 1
    if paragraph.endswith("다") or paragraph.endswith("다."):
        rule_score += 1

    scores = {"case": case_score, "rule": rule_score, "concept": concept_score}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "concept"
    return best


def format_with_section(paragraph: str, section: Optional[str]) -> str:
    """섹션 정보가 있을 경우 보기 좋게 꾸며준다."""

    if section:
        section_clean = section.strip()
        if not paragraph.startswith(section_clean):
            return f"[{section_clean}] {paragraph}".strip()
    return paragraph.strip()

