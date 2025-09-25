"""Utility helpers for natural-language aware document parsing.

This module consolidates text pre-processing and heuristic classification
logic so that the different parsing strategies (rule-based, ML-assisted and
hybrid) can share the same natural language friendly behaviour.

추가로, 정형/비정형 문서에서 클래스 구조(클래스명, 속성, 메소드 등)를
추출하기 위한 도우미를 포함한다. JSON, XML, CSV와 같은 정형 데이터는 각
포맷 전용 파서를 활용하고, 일반 텍스트는 정규표현식 기반의 간단한 NLP
접근을 사용한다.
"""

from __future__ import annotations

import csv
import io
import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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


# ---------------------------------------------------------------------------
# 클래스 정보 추출 (정형/비정형 문서 지원)
# ---------------------------------------------------------------------------


CLASS_NAME_KEYS = {
    "class",
    "classname",
    "class_name",
    "name",
    "클래스",
    "클래스명",
}

ATTRIBUTE_KEYS = {
    "attributes",
    "attribute",
    "attrs",
    "properties",
    "fields",
    "속성",
    "특성",
}

METHOD_KEYS = {
    "methods",
    "method",
    "functions",
    "function",
    "operations",
    "메소드",
    "메서드",
    "함수",
}


def detect_document_format(text: str) -> str:
    """간단한 휴리스틱으로 문서 형식을 판별한다."""

    stripped = text.strip()
    if not stripped:
        return "text"

    # JSON 판별
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return "json"
        except json.JSONDecodeError:
            pass

    # XML 판별
    if stripped.startswith("<") and stripped.endswith(">"):
        try:
            ET.fromstring(stripped)
            return "xml"
        except ET.ParseError:
            pass

    # CSV 판별 (구분자 기반)
    lines = stripped.splitlines()
    if len(lines) >= 2 and any("," in line or ";" in line or "\t" in line for line in lines[:5]
    ):
        sample = "\n".join(lines[:10])
        try:
            csv.Sniffer().sniff(sample)
            return "csv"
        except csv.Error:
            pass

    return "text"


def _normalize_to_list(value: Any) -> List[str]:
    """다양한 타입의 값을 문자열 리스트로 변환한다."""

    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"[;,\n]\s*", value)
        return [part.strip() for part in parts if part.strip()]
    if isinstance(value, dict):
        items: List[str] = []
        for key, val in value.items():
            normalized_val = _normalize_to_list(val)
            if normalized_val:
                items.append(f"{key}: {', '.join(normalized_val)}")
        return items
    if isinstance(value, (list, tuple, set)):
        items = []
        for item in value:
            if isinstance(item, (dict, list, tuple, set)):
                items.extend(_normalize_to_list(item))
            else:
                text = str(item).strip()
                if text:
                    items.append(text)
        return items
    return [str(value).strip()]


def _deduplicate_strings(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for value in values:
        if value not in seen and value:
            ordered.append(value)
            seen.add(value)
    return ordered


def _candidate_from_mapping(mapping: Dict[Any, Any]) -> Optional[Dict[str, List[str]]]:
    name: Optional[str] = None
    attributes: List[str] = []
    methods: List[str] = []

    for key, value in mapping.items():
        key_lower = str(key).lower()
        if key_lower in CLASS_NAME_KEYS and not name:
            name = str(value).strip()
        elif key_lower in ATTRIBUTE_KEYS:
            attributes.extend(_normalize_to_list(value))
        elif key_lower in METHOD_KEYS:
            methods.extend(_normalize_to_list(value))

    if name and (attributes or methods):
        return {
            "name": name,
            "attributes": _deduplicate_strings(attributes),
            "methods": _deduplicate_strings(methods),
        }
    return None


def _walk_structured_data(data: Any) -> List[Dict[str, List[str]]]:
    results: List[Dict[str, List[str]]] = []
    if isinstance(data, dict):
        candidate = _candidate_from_mapping(data)
        if candidate:
            results.append(candidate)
        for value in data.values():
            results.extend(_walk_structured_data(value))
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            results.extend(_walk_structured_data(item))
    return results


def _extract_from_json(text: str) -> List[Dict[str, List[str]]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return _walk_structured_data(data)


def _extract_from_csv(text: str) -> List[Dict[str, List[str]]]:
    buffer = io.StringIO(text)
    try:
        sample = buffer.read(1024)
        buffer.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        buffer.seek(0)
    except csv.Error:
        buffer.seek(0)
        dialect = csv.excel

    reader = csv.DictReader(buffer, dialect=dialect)
    if not reader.fieldnames:
        return []

    results: List[Dict[str, List[str]]] = []
    lowered_fields = {field.lower(): field for field in reader.fieldnames}

    class_field = next(
        (lowered_fields[field] for field in lowered_fields if field in CLASS_NAME_KEYS),
        None,
    )
    attribute_fields = [
        lowered_fields[field]
        for field in lowered_fields
        if field in ATTRIBUTE_KEYS or "attribute" in field or "속성" in field
    ]
    method_fields = [
        lowered_fields[field]
        for field in lowered_fields
        if field in METHOD_KEYS or "method" in field or "메소드" in field or "메서드" in field
    ]

    if not class_field:
        return []

    for row in reader:
        name_raw = row.get(class_field)
        if not name_raw:
            continue
        attributes: List[str] = []
        methods: List[str] = []
        for field in attribute_fields:
            attributes.extend(_normalize_to_list(row.get(field)))
        for field in method_fields:
            methods.extend(_normalize_to_list(row.get(field)))
        if attributes or methods:
            results.append(
                {
                    "name": str(name_raw).strip(),
                    "attributes": _deduplicate_strings(attributes),
                    "methods": _deduplicate_strings(methods),
                }
            )

    return results


def _extract_from_xml(text: str) -> List[Dict[str, List[str]]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    results: List[Dict[str, List[str]]] = []

    def walk(element: ET.Element) -> None:
        tag_lower = element.tag.lower()
        name: Optional[str] = None
        if "class" in tag_lower or "클래스" in tag_lower:
            name = element.attrib.get("name") or element.attrib.get("id")
        if not name:
            name_elem = element.find("name")
            if name_elem is not None and name_elem.text:
                name = name_elem.text.strip()

        attributes: List[str] = []
        methods: List[str] = []

        for child in element:
            child_tag = child.tag.lower()
            if (
                child_tag in ATTRIBUTE_KEYS
                or "attribute" in child_tag
                or "속성" in child_tag
            ):
                if child.text:
                    attributes.extend(_normalize_to_list(child.text))
                attributes.extend(_normalize_to_list(child.attrib))
                for grand in child:
                    if grand.text:
                        attributes.extend(_normalize_to_list(grand.text))
                    attributes.extend(_normalize_to_list(grand.attrib))
            elif (
                child_tag in METHOD_KEYS
                or "method" in child_tag
                or "메소드" in child_tag
                or "메서드" in child_tag
            ):
                if child.text:
                    methods.extend(_normalize_to_list(child.text))
                methods.extend(_normalize_to_list(child.attrib))
                for grand in child:
                    if grand.text:
                        methods.extend(_normalize_to_list(grand.text))
                    methods.extend(_normalize_to_list(grand.attrib))

        if name and (attributes or methods):
            results.append(
                {
                    "name": name.strip(),
                    "attributes": _deduplicate_strings(attributes),
                    "methods": _deduplicate_strings(methods),
                }
            )

        for child in element:
            walk(child)

    walk(root)
    return results


CLASS_NAME_PATTERN = re.compile(
    r"(?:클래스명?|class(?:\s*name)?)\s*[:：]\s*(?P<name>[\w가-힣一-龥_][\w가-힣一-龥_\s]*)",
    re.IGNORECASE,
)

ATTRIBUTE_TEXT_PATTERNS = [
    re.compile(r"(?:속성|attributes?)\s*(?:은|는|:)?\s*(?P<body>[^\.\n]+)", re.IGNORECASE),
    re.compile(r"주요 속성은\s*(?P<body>[^\.\n]+)", re.IGNORECASE),
]

METHOD_TEXT_PATTERNS = [
    re.compile(r"(?:메소드|메서드|methods?)\s*(?:은|는|:)?\s*(?P<body>[^\.\n]+)", re.IGNORECASE),
    re.compile(r"제공(?:하는|되는)?\s*(?:메소드|메서드|functions?)\s*(?:은|는)?\s*(?P<body>[^\.\n]+)", re.IGNORECASE),
]


def _update_info_from_text(info: Dict[str, List[str]], paragraph: str) -> bool:
    updated = False
    for pattern in ATTRIBUTE_TEXT_PATTERNS:
        match = pattern.search(paragraph)
        if match:
            attributes = _normalize_to_list(match.group("body"))
            if attributes:
                info["attributes"].extend(attributes)
                updated = True
    for pattern in METHOD_TEXT_PATTERNS:
        match = pattern.search(paragraph)
        if match:
            methods = _normalize_to_list(match.group("body"))
            if methods:
                info["methods"].extend(methods)
                updated = True
    return updated


def _extract_from_text(text: str) -> List[Dict[str, List[str]]]:
    normalized = normalize_text(text)
    paragraphs = split_into_paragraphs(normalized)

    results: List[Dict[str, List[str]]] = []
    current: Optional[Dict[str, List[str]]] = None

    for paragraph in paragraphs:
        match = CLASS_NAME_PATTERN.search(paragraph)
        if match:
            if current and (current["attributes"] or current["methods"]):
                current["attributes"] = _deduplicate_strings(current["attributes"])
                current["methods"] = _deduplicate_strings(current["methods"])
                results.append(current)
            name = match.group("name").strip()
            current = {"name": name, "attributes": [], "methods": []}
            remainder = paragraph[match.end() :]
            if remainder:
                _update_info_from_text(current, remainder)
            continue

        if current is None:
            # 클래스 선언 없이도 속성/메소드 정보를 제공하는 경우는 무시
            continue

        if _update_info_from_text(current, paragraph):
            continue

        # Bullet list 지원 ("- name" 등)
        if paragraph.startswith("-") or paragraph.startswith("•"):
            bullet_item = paragraph.lstrip("-• ")
            if any(keyword in bullet_item for keyword in ("()", "메소드", "메서드")):
                current["methods"].extend(_normalize_to_list(bullet_item))
            else:
                current["attributes"].extend(_normalize_to_list(bullet_item))

    if current and (current["attributes"] or current["methods"]):
        current["attributes"] = _deduplicate_strings(current["attributes"])
        current["methods"] = _deduplicate_strings(current["methods"])
        results.append(current)

    deduped: List[Dict[str, List[str]]] = []
    seen = set()
    for info in results:
        key = (
            info["name"],
            tuple(info["attributes"]),
            tuple(info["methods"]),
        )
        if key in seen:
            continue
        deduped.append(info)
        seen.add(key)
    return deduped


def extract_class_information(text: str) -> List[Dict[str, List[str]]]:
    """클래스 구조 정보를 문서에서 추출한다."""

    document_type = detect_document_format(text)
    if document_type == "json":
        infos = _extract_from_json(text)
    elif document_type == "xml":
        infos = _extract_from_xml(text)
    elif document_type == "csv":
        infos = _extract_from_csv(text)
    else:
        infos = _extract_from_text(text)

    normalized_infos: List[Dict[str, List[str]]] = []
    for info in infos:
        name = info.get("name", "").strip()
        attributes = _deduplicate_strings(info.get("attributes", []))
        methods = _deduplicate_strings(info.get("methods", []))
        if not name or (not attributes and not methods):
            continue
        normalized_infos.append({"name": name, "attributes": attributes, "methods": methods})

    return normalized_infos


def format_class_summary(info: Dict[str, List[str]]) -> str:
    """추출된 클래스 정보를 자연어 요약으로 변환한다."""

    name = info.get("name", "").strip()
    if not name:
        return ""

    attributes = _deduplicate_strings(info.get("attributes", []))
    methods = _deduplicate_strings(info.get("methods", []))

    parts: List[str] = []
    if attributes:
        parts.append(f"속성: {', '.join(attributes)}")
    if methods:
        parts.append(f"메소드: {', '.join(methods)}")

    if parts:
        return f"클래스 {name} - {' | '.join(parts)}"
    return f"클래스 {name}"

