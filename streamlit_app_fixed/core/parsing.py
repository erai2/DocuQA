# core/parsing.py
import re
import pandas as pd

def parse_document(text: str):
    """규칙 기반 파서"""
    rules, cases, concepts = [], [], []

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        if any(kw in line for kw in ["合", "沖", "冲", "刑", "破", "穿", "入墓", "墓庫"]):
            rules.append({"id": f"rule_{len(rules)+1}", "desc": line})
        elif re.search(r"[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]", line):
            cases.append({"id": f"case_{len(cases)+1}", "detail": line})
        elif any(kw in line for kw in ["祿", "元神", "原神", "帶象", "幻象", "空亡", "驛馬"]):
            concepts.append({"id": f"concept_{len(concepts)+1}", "desc": line})

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
