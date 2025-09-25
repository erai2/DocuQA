from core.ai_utils import clean_text_with_ai
from core.text_parsing_utils import (
    classify_paragraph,
    format_with_section,
    iter_structured_paragraphs,
)


def parse_document_hybrid(text: str):
    """Hybrid 파서: 규칙 기반 + AI 보조 (자연어 문단 기반)"""

    cases, rules, concepts = [], [], []

    for idx, record in enumerate(iter_structured_paragraphs(text)):
        paragraph = record.get("paragraph", "").strip()
        if not paragraph:
            continue
        section = record.get("section")
        category = classify_paragraph(paragraph, section)
        cleaned = clean_text_with_ai(paragraph)[:500]
        formatted = format_with_section(cleaned, section)

        if category == "case":
            cases.append({"id": f"hyb_case_{idx}", "detail": formatted})
        elif category == "rule":
            rules.append({"id": f"hyb_rule_{idx}", "desc": formatted})
        else:
            concepts.append({"id": f"hyb_concept_{idx}", "desc": formatted})

    return cases, rules, concepts
