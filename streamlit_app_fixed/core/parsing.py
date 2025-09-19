import os
from typing import Dict, List, Optional, Tuple

import pandas as pd


ParsedSection = Dict[str, str]


def parse_document(text: str) -> Tuple[List[ParsedSection], List[ParsedSection], List[ParsedSection]]:
    """간단한 규칙 기반 문서 파서.

    텍스트를 사례(case), 규칙(rule), 개념(concept) 세 가지 범주로 나누어
    각 항목의 제목과 설명을 추출한다. 명시적인 구분자가 없을 경우에는
    일반 텍스트를 개념으로 처리하여 반환한다.
    """

    if not isinstance(text, str) or not text.strip():
        return [], [], []

    cases: List[ParsedSection] = []
    rules: List[ParsedSection] = []
    concepts: List[ParsedSection] = []

    current_type: Optional[str] = None
    current_title: str = ""
    buffer: List[str] = []

    def flush_buffer():
        nonlocal buffer, current_type, current_title
        if not buffer:
            current_title = ""
            return

        content = "\n".join(buffer).strip()
        buffer = []

        if not content:
            current_title = ""
            return

        title = current_title or {
            "case": "사례",
            "rule": "규칙",
            "concept": "개념",
        }.get(current_type or "concept", "내용")

        if current_type == "case":
            cases.append({"title": title, "detail": content})
        elif current_type == "rule":
            rules.append({"title": title, "desc": content})
        else:
            concepts.append({"title": title, "desc": content})

        current_title = ""

    keyword_map = {
        "사례": "case",
        "case": "case",
        "규칙": "rule",
        "rule": "rule",
        "개념": "concept",
        "concept": "concept",
        "정의": "concept",
    }

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        lowered = line.lower()
        matched_type: Optional[str] = None
        matched_keyword: Optional[str] = None

        for keyword, section_type in keyword_map.items():
            if lowered.startswith(keyword):
                matched_type = section_type
                matched_keyword = keyword
                break

        if matched_type:
            flush_buffer()
            current_type = matched_type

            stripped_line = line.strip()

            if ":" in stripped_line:
                title, remainder = stripped_line.split(":", 1)
                current_title = title.strip()
                if remainder.strip():
                    buffer.append(remainder.strip())
            elif "-" in stripped_line and not stripped_line.startswith("-"):
                title, remainder = stripped_line.split("-", 1)
                current_title = title.strip()
                if remainder.strip():
                    buffer.append(remainder.strip())
            else:
                keyword_length = len(matched_keyword) if matched_keyword else 0
                current_title = stripped_line[keyword_length:].strip() or matched_type
            continue

        if line.startswith(("-", "*", "•")):
            item_text = line.lstrip("-*•").strip()
            if not current_type:
                current_type = "concept"
            buffer.append(item_text)
        else:
            if not current_type:
                current_type = "concept"
            buffer.append(line)

    flush_buffer()

    return cases, rules, concepts


def parse_and_store_documents(file_path: str) -> pd.DataFrame:
    """문서를 파싱하고 파싱 결과를 DataFrame으로 저장한다."""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        cases, rules, concepts = parse_document(content)

        rows = []
        filename = os.path.basename(file_path)

        for idx, case in enumerate(cases, start=1):
            detail = case.get("detail", "").strip()
            if not detail:
                continue
            rows.append(
                {
                    "filename": filename,
                    "category": "case",
                    "title": case.get("title", f"사례 {idx}"),
                    "content": detail,
                }
            )

        for idx, rule in enumerate(rules, start=1):
            desc = rule.get("desc", "").strip()
            if not desc:
                continue
            rows.append(
                {
                    "filename": filename,
                    "category": "rule",
                    "title": rule.get("title", f"규칙 {idx}"),
                    "content": desc,
                }
            )

        for idx, concept in enumerate(concepts, start=1):
            desc = concept.get("desc", "").strip()
            if not desc:
                continue
            rows.append(
                {
                    "filename": filename,
                    "category": "concept",
                    "title": concept.get("title", f"개념 {idx}"),
                    "content": desc,
                }
            )

        df = pd.DataFrame(rows)

        parsed_csv = "data/parsed_docs.csv"
        os.makedirs("data", exist_ok=True)

        if not df.empty:
            if os.path.exists(parsed_csv):
                old_df = pd.read_csv(parsed_csv)
                combined = pd.concat([old_df, df], ignore_index=True).drop_duplicates()
            else:
                combined = df
            combined.to_csv(parsed_csv, index=False, encoding="utf-8-sig")

        return df

    except Exception as e:
        print(f"[ERROR] parse_and_store_documents 실패: {e}")
        return pd.DataFrame()
