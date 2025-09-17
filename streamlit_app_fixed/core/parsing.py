# core/parsing.py
import os
import glob
import pandas as pd
import re

def parse_text_file(file_path: str) -> str:
    """텍스트/마크다운 파일을 읽어서 문자열 반환"""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def parse_document(text: str):
    """
    텍스트 문서를 분석해서 cases, rules, concepts 리스트로 분리
    - <사례>, <규칙>, <개념> 태그가 있으면 태그 기반 파싱
    - 없으면 키워드 기반 단순 분류
    """
    cases, rules, concepts = [], [], []

    # 태그 기반
    if any(tag in text for tag in ["<사례>", "<규칙>", "<개념>"]):
        current_type, buffer = None, []

        def flush():
            nonlocal current_type, buffer
            if not buffer:
                return
            content = " ".join(buffer).strip()
            if current_type == "사례":
                cases.append({"title": f"사례-{len(cases)+1}", "detail": content})
            elif current_type == "규칙":
                rules.append({"name": f"규칙-{len(rules)+1}", "desc": content})
            elif current_type == "개념":
                concepts.append({"keyword": f"개념-{len(concepts)+1}", "desc": content})
            buffer = []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("<사례>"):
                flush(); current_type = "사례"; buffer = []
            elif line.startswith("<규칙>"):
                flush(); current_type = "규칙"; buffer = []
            elif line.startswith("<개념>"):
                flush(); current_type = "개념"; buffer = []
            elif line.startswith("</"):
                flush(); current_type = None
            else:
                buffer.append(line)
        flush()

    # 키워드 기반 (fallback)
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if "사례" in line or "예시" in line:
                cases.append({"title": f"사례-{len(cases)+1}", "detail": line})
            elif "규칙" in line or "경우" in line or "된다" in line:
                rules.append({"name": f"규칙-{len(rules)+1}", "desc": line})
            else:
                # "키워드: 설명" 패턴 탐지
                parts = re.split(r"[:\-•]", line, 1)
                if len(parts) == 2:
                    concepts.append({"keyword": parts[0].strip(), "desc": parts[1].strip()})
                else:
                    concepts.append({"keyword": f"개념-{len(concepts)+1}", "desc": line})

    return cases, rules, concepts


def parse_and_store_documents(file_paths, output_dir="data/raw_docs"):
    """
    여러 텍스트/마크다운 파일을 자동 파싱하여 CSV로 저장.
    Streamlit에서 업로드 후 호출됨.
    """
    os.makedirs(output_dir, exist_ok=True)
    records = []

    for file_path in file_paths:
        try:
            text = parse_text_file(file_path)
            cases, rules, concepts = parse_document(text)
            if cases:
                for c in cases:
                    records.append({"source": os.path.basename(file_path), "type": "case", "content": c})
            if rules:
                for r in rules:
                    records.append({"source": os.path.basename(file_path), "type": "rule", "content": r})
            if concepts:
                for c in concepts:
                    records.append({"source": os.path.basename(file_path), "type": "concept", "content": c})
        except Exception as e:
            print(f"[ERROR] {file_path} 읽기 실패: {e}")

    if records:
        df = pd.DataFrame(records)
        out_path = os.path.join(output_dir, "parsed_docs.csv")

        # 기존 CSV 있으면 append
        if os.path.exists(out_path):
            old_df = pd.read_csv(out_path)
            df = pd.concat([old_df, df], ignore_index=True).drop_duplicates(subset=["content"])

        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    return None


def auto_parse_existing_docs(input_dir="data/raw_docs", output_dir="data/raw_docs"):
    """
    data/raw_docs 안에 있는 모든 txt/md 파일 자동 파싱
    """
    files = glob.glob(os.path.join(input_dir, "*.txt")) + glob.glob(os.path.join(input_dir, "*.md"))
    return parse_and_store_documents(files, output_dir=output_dir)
