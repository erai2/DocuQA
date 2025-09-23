# core/parsing.py
import re
import pandas as pd

def parse_document(text: str):
    """
    입력 텍스트를 (규칙, 사례, 용어) 세 가지로 분류해서 반환.
    """
    rules, cases, concepts = [], [], []

    # 줄 단위 분리
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        # 규칙 패턴 (합, 충, 형, 파, 천, 묘고 등)
        if any(kw in line for kw in ["合", "沖", "冲", "刑", "破", "穿", "入墓", "墓庫"]):
            rules.append({
                "id": f"rule_{len(rules)+1}",
                "desc": line
            })
        # 사례 패턴 (사주팔자 예시: 간지 포함 여부)
        elif re.search(r"[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]", line):
            cases.append({
                "id": f"case_{len(cases)+1}",
                "detail": line
            })
        # 용어 패턴 (록, 원신, 대상, 환상 등)
        elif any(kw in line for kw in ["祿", "元神", "原神", "帶象", "幻象", "空亡", "驛馬"]):
            concepts.append({
                "id": f"concept_{len(concepts)+1}",
                "desc": line
            })

    return cases, rules, concepts


def parse_and_store_documents(path: str) -> pd.DataFrame:
    """
    파일을 읽어서 파싱하고, 하나의 DataFrame으로 반환.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    cases, rules, concepts = parse_document(text)

    # 세 가지를 합쳐서 DataFrame 생성
    rows = []
    for c in cases:
        rows.append({"type": "case", "id": c["id"], "content": c["detail"]})
    for r in rules:
        rows.append({"type": "rule", "id": r["id"], "content": r["desc"]})
    for c in concepts:
        rows.append({"type": "concept", "id": c["id"], "content": c["desc"]})

    df = pd.DataFrame(rows)
    return df
