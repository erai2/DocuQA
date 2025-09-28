"""Streamlit entrypoint for the Suri Q&AI application."""

import os
from io import StringIO
from typing import Dict, Iterable, List
import pandas as pd
import streamlit as st

from core.ai_engine import generate_ai_response, summarize_by_keywords, summarize_long_csv
from core.ai_utils import clean_text_with_ai
from core.database import ensure_db, insert_csv_to_db, load_csv_files, load_csv_from_db, list_tables
from core.hybrid_search import hybrid_search
from core.rag import build_databases
from profiles_page import profiles_page


DATA_DIR = "data"
RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_docs")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
PARSED_CSV_PATH = os.path.join(DATA_DIR, "parsed_docs.csv")

# === 수암명리 전용 태그 ===
RULE_CATEGORIES = ["궁위", "허투", "대상", "묘고", "상호작용"]
PRIORITY_LEVELS = ["1. 구조 결정", "2. 특수 구조", "3. 허투/입묘", "4. 일반론"]
CASE_FOCUS_TOPICS = ["직업/사회운", "가족/육친", "재물운", "건강/학업운"]


def configure_app():
    st.set_page_config(page_title="Suri Q&AI", layout="wide")
    st.title("📊 Suri Q&AI")
    ensure_directories([DATA_DIR, RAW_DOCS_DIR, VECTOR_DB_DIR])
    ensure_db()


def ensure_directories(paths: Iterable[str]):
    for path in paths:
        os.makedirs(path, exist_ok=True)


# ----------------------------
# 문서 업로드
# ----------------------------
def render_upload_section():
    st.header("📑 문서 업로드 및 파싱")

    parser_mode = st.radio("파서 모드 선택", ["규칙 기반", "AI 보조", "Hybrid"], horizontal=True)
    uploaded_files = st.file_uploader("txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True)

    if not uploaded_files:
        return

    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read().decode("utf-8")
        st.subheader(f"📄 {uploaded_file.name}")
        st.text_area("파일 내용 미리보기", file_content[:1000], height=200)

        if not st.button(f"파싱 실행: {uploaded_file.name}"):
            continue

        save_path = os.path.join(RAW_DOCS_DIR, uploaded_file.name)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        parsed_df = parse_document_by_mode(file_content, parser_mode)
        if parsed_df.empty:
            st.warning("⚠️ 파싱 결과 없음")
            continue

        st.success("✅ 파싱 완료, AI 교정 중...")
        raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")
        cleaned_df = clean_dataframe_with_ai(raw_text, parsed_df)

        st.success("✅ AI 교정 완료, 수정 가능")
        edited_df = st.data_editor(cleaned_df, num_rows="dynamic", use_container_width=True)

        if st.button(f"{uploaded_file.name} 저장", key=f"save_{uploaded_file.name}"):
            combined = merge_with_existing_csv(edited_df)
            combined.to_csv(PARSED_CSV_PATH, index=False, encoding="utf-8-sig")
            insert_csv_to_db(combined, "parsed_docs")
            st.success(f"📦 DB 저장 완료 (총 {len(combined)}행)")


def parse_document_by_mode(file_content: str, parser_mode: str) -> pd.DataFrame:
    rows: List[Dict[str, str]] = []
    if "규칙" in parser_mode:
        from core.parsing import parse_document
        cases, rules, concepts = parse_document(file_content)
    elif "AI" in parser_mode:
        from core.parse_document_ml import parse_document_ml
        cases, rules, concepts = parse_document_ml(file_content)
    else:
        from core.parse_document_hybrid import parse_document_hybrid
        cases, rules, concepts = parse_document_hybrid(file_content)

    for c in cases:
        rows.append({"type": "case", "id": c["id"], "content": c.get("detail", "")})
    for r in rules:
        rows.append({"type": "rule", "id": r["id"], "content": r.get("desc", "")})
    for c in concepts:
        rows.append({"type": "concept", "id": c["id"], "content": c.get("desc", "")})
    return pd.DataFrame(rows)


def clean_dataframe_with_ai(raw_text, fallback_df):
    cleaned_text = clean_text_with_ai(raw_text)
    try:
        return pd.read_csv(StringIO(cleaned_text))
    except:
        return fallback_df


def merge_with_existing_csv(edited_df):
    if os.path.exists(PARSED_CSV_PATH):
        old_df = pd.read_csv(PARSED_CSV_PATH)
        combined = pd.concat([old_df, edited_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["type", "id", "content"])
        return combined
    return edited_df


# ----------------------------
# DB 미리보기
# ----------------------------
def render_db_preview():
    st.header("📦 DB 미리보기")
    if st.button("DB 불러오기"):
        db_df = load_csv_from_db("parsed_docs")
        if db_df.empty:
            st.warning("⚠️ DB 비어있음")
        else:
            st.dataframe(db_df, use_container_width=True)


# ----------------------------
# 요약
# ----------------------------
def render_summary():
    st.header("📝 CSV 요약")
    if st.button("CSV 전체 요약"):
        csv_text = build_combined_csv_text()
        if not csv_text:
            return st.warning("데이터 없음")
        summary, parts = summarize_long_csv(csv_text)
        st.text_area("요약 결과", summary, height=300)


def build_combined_csv_text():
    csv_dfs = load_csv_files(DATA_DIR)
    if not csv_dfs:
        return ""
    combined = pd.concat(list(csv_dfs.values()), ignore_index=True)
    return combined.to_csv(index=False, encoding="utf-8-sig")


# ----------------------------
# 상담
# ----------------------------
def render_ai_consultation():
    st.header("💬 상담")
    query = st.text_input("질문 입력")
    if st.button("AI 응답"):
        if not query.strip():
            return st.warning("질문 없음")
        docs = hybrid_search(query, db_dir=VECTOR_DB_DIR, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = generate_ai_response(f"{query}\n\n참고자료:\n{context}")
        st.markdown(answer)


# ----------------------------
# DB 관리
# ----------------------------
def render_db_manage():
    st.header("🗂️ DB 관리")
    if st.button("테이블 목록"):
        st.write(list_tables())


# ----------------------------
# Main
# ----------------------------
def main():
    configure_app()
    choice = st.sidebar.radio("페이지 선택", ["문서 관리", "DB 미리보기", "요약", "상담", "프로필"])
    if choice == "문서 관리":
        render_upload_section()
    elif choice == "DB 미리보기":
        render_db_preview()
    elif choice == "요약":
        render_summary()
    elif choice == "상담":
        render_ai_consultation()
    elif choice == "프로필":
        profiles_page()
    else:
        render_db_manage()


if __name__ == "__main__":
    main()
