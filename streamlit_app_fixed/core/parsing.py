# core/parsing.py
import pandas as pd

from core.text_parsing_utils import (
    classify_paragraph,
    extract_class_information,
    format_class_summary,
    format_with_section,
    iter_structured_paragraphs,
)


def parse_document(text: str):
    """규칙 기반 파서 (자연어 문단 기반)"""

    rules, cases, concepts = [], [], []
    counts = {"case": 0, "rule": 0, "concept": 0}

    for record in iter_structured_paragraphs(text):
        paragraph = record.get("paragraph", "").strip()
        if not paragraph:
            continue
        section = record.get("section")
        category = classify_paragraph(paragraph, section)
        counts[category] += 1
        formatted = format_with_section(paragraph, section)

        if category == "case":
            cases.append({"id": f"case_{counts['case']}", "detail": formatted})
        elif category == "rule":
            rules.append({"id": f"rule_{counts['rule']}", "desc": formatted})
        else:
            concepts.append({"id": f"concept_{counts['concept']}", "desc": formatted})

    # 클래스 구조 요약을 concept 카테고리에 추가한다.
    for info in extract_class_information(text):
        summary = format_class_summary(info)
        if not summary:
            continue
        counts["concept"] += 1
        concepts.append(
            {
                "id": f"concept_{counts['concept']}",
                "desc": summary,
                "meta": info,
            }
        )

    return cases, rules, concepts


def parse_and_store_documents(path: str) -> pd.DataFrame:
    """규칙 기반 파서를 실행하고 DataFrame 반환"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    cases, rules, concepts = parse_document(text)

    rows = []
    for c in cases:
        rows.append({"type": "case", "id": c["id"], "content": c["detail"]})
    for r in rules:
        rows.append({"type": "rule", "id": r["id"], "content": r["desc"]})
    for c in concepts:
        rows.append({"type": "concept", "id": c["id"], "content": c["desc"]})

    return pd.DataFrame(rows)
