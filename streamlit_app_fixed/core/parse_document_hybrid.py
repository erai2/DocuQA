# core/parse_document_hybrid.py
import re
import pandas as pd
from core.ai_engine import clean_text_with_ai

def parse_document_hybrid(text: str):
    """
    Hybrid 파서: 규칙 기반 분류 + AI 보조 요약
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cases, rules, concepts = [], [], []

    for idx, line in enumerate(lines):
        if "사례" in line or line.startswith("<사례"):
            cases.append({"id": f"hyb_case_{idx}", "detail": clean_text_with_ai(line)[:500]})
        elif "격" in line or "법" in line or "조건" in line:
            rules.append({"id": f"hyb_rule_{idx}", "desc": clean_text_with_ai(line)[:500]})
        elif "정의" in line or "개념" in line:
            concepts.append({"id": f"hyb_concept_{idx}", "desc": clean_text_with_ai(line)[:500]})
        else:
            # AI 보조로 자동 분류
            guess = clean_text_with_ai(line)[:500]
            concepts.append({"id": f"hyb_misc_{idx}", "desc": guess})

    return cases, rules, concepts
