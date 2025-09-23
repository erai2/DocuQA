# core/parse_document_ml.py
import re
import pandas as pd
from core.ai_engine import clean_text_with_ai

def parse_document_ml(text: str):
    """
    AI 보조 파서: 문장을 AI 교정/요약해서 분류
    """
    # 기본적으로 rule / case / concept 키워드 단위로 나눔
    chunks = re.split(r'\n+', text)
    cases, rules, concepts = [], [], []

    for idx, chunk in enumerate(chunks):
        cleaned = clean_text_with_ai(chunk)[:1000]  # 토큰 과부하 방지
        if "사례" in chunk or "예시" in chunk:
            cases.append({"id": f"ml_case_{idx}", "detail": cleaned})
        elif "규칙" in chunk or "조건" in chunk:
            rules.append({"id": f"ml_rule_{idx}", "desc": cleaned})
        elif "정의" in chunk or "개념" in chunk:
            concepts.append({"id": f"ml_concept_{idx}", "desc": cleaned})

    return cases, rules, concepts
