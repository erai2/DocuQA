# core/parsing.py
import os
import pandas as pd

def parse_document(text: str):
    """
    단일 문서(text)를 파싱하여 (cases, rules, concepts) 반환
    """
    cases, rules, concepts = [], [], []

    # 간단한 분류 예시 (확장 가능)
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("사례"):
            cases.append({"detail": line})
        elif line.startswith("규칙"):
            rules.append({"desc": line})
        else:
            concepts.append({"desc": line})

    return cases, rules, concepts


def parse_and_store_documents(file_paths, output_csv="data/parsed_docs.csv"):
    """
    여러 문서 파일(txt, md 등)을 읽어와서 파싱 → CSV 저장
    """
    all_cases, all_rules, all_concepts = [], [], []

    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            cases, rules, concepts = parse_document(text)
            all_cases.extend(cases)
            all_rules.extend(rules)
            all_concepts.extend(concepts)
        except Exception as e:
            print(f"[ERROR] {path} 처리 실패: {e}")

    # CSV 저장
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", encoding="utf-8") as f:
        f.write("type,content\n")
        for c in all_cases:
            f.write(f"case,{c['detail']}\n")
        for r in all_rules:
            f.write(f"rule,{r['desc']}\n")
        for c in all_concepts:
            f.write(f"concept,{c['desc']}\n")

    print(f"[INFO] ✅ CSV 저장 완료 → {output_csv}")
    return all_cases, all_rules, all_concepts
