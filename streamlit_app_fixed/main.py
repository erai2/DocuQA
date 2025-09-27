"""Streamlit entrypoint for the Suri Q&AI application."""

from __future__ import annotations

import os
from io import StringIO
from typing import Dict, Iterable, List

import pandas as pd
import streamlit as st

from core.ai_engine import generate_ai_response, summarize_by_keywords, summarize_long_csv
from core.ai_utils import clean_text_with_ai
from core.database import (
    ensure_db,
    insert_csv_to_db,
    load_csv_files,
    load_csv_from_db,
    list_tables,
)
from core.rag import build_databases
from profiles_page import profiles_page


DATA_DIR = "data"
RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_docs")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
PARSED_CSV_PATH = os.path.join(DATA_DIR, "parsed_docs.csv")


def configure_app() -> None:
    """Set default layout information and bootstrap directories/database."""

    st.set_page_config(page_title="Suri Q&AI", layout="wide")
    st.title("📊 Suri Q&AI (최신 OpenAI API 버전)")

    ensure_directories([DATA_DIR, RAW_DOCS_DIR, VECTOR_DB_DIR])
    ensure_db()


def ensure_directories(paths: Iterable[str]) -> None:
    """Create directories required by the application if they do not exist."""

    for path in paths:
        os.makedirs(path, exist_ok=True)


def render_document_management_page() -> None:
    """Render the document management workflow."""

    render_upload_section()
    render_db_preview_section()
    render_csv_summary_section()
    render_keyword_summary_section()
    render_ai_consultation_section()
    render_database_build_section()
    render_database_management_section()


def render_upload_section() -> None:
    st.header("📑 새 문서 업로드 및 파싱")

    parser_mode = st.radio(
        "파서 모드 선택",
        ["1단계: 규칙 기반 (빠름)", "2단계: AI 보조 (정밀)", "3단계: Hybrid (효율적)"],
        horizontal=True,
    )

    uploaded_files = st.file_uploader(
        "txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True
    )

    if not uploaded_files:
        return

    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read().decode("utf-8")
        st.subheader(f"📄 {uploaded_file.name}")
        st.text_area("파일 내용 미리보기", file_content[:1000], height=200)

        if not st.button(f"이 문서 파싱하기: {uploaded_file.name}"):
            continue

        save_path = os.path.join(RAW_DOCS_DIR, uploaded_file.name)
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(file_content)

        parsed_df = parse_document_by_mode(file_content, parser_mode)
        if parsed_df.empty:
            st.warning("⚠️ 파싱 결과가 없습니다.")
            continue

        st.success("✅ 파싱 완료, AI 교정 적용 중...")

        raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")
        cleaned_df = clean_dataframe_with_ai(raw_text, parsed_df)

        st.success("✅ AI 교정 완료! 아래에서 직접 수정 후 저장하세요.")
        edited_df = st.data_editor(cleaned_df, num_rows="dynamic", use_container_width=True)

        if st.button(f"{uploaded_file.name} 저장", key=f"save_{uploaded_file.name}"):
            combined = merge_with_existing_csv(edited_df)
            combined.to_csv(PARSED_CSV_PATH, index=False, encoding="utf-8-sig")
            st.success(f"📂 parsed_docs.csv 저장 완료 (총 {len(combined)}행) ✅")

            total_rows = insert_csv_to_db(combined, table_name="parsed_docs")
            st.success(f"📦 DB 저장 완료: {total_rows}행 (중복 제거 후)")


def parse_document_by_mode(file_content: str, parser_mode: str) -> pd.DataFrame:
    """Parse documents using the selected parsing strategy."""

    rows: List[Dict[str, str]] = []

    if "규칙 기반" in parser_mode:
        from core.parsing import parse_document

        cases, rules, concepts = parse_document(file_content)
    elif "AI 보조" in parser_mode:
        from core.parse_document_ml import parse_document_ml

        cases, rules, concepts = parse_document_ml(file_content)
    else:
        from core.parse_document_hybrid import parse_document_hybrid

        cases, rules, concepts = parse_document_hybrid(file_content)

    for case in cases:
        rows.append({"type": "case", "id": case["id"], "content": case.get("detail", "")})
    for rule in rules:
        rows.append({"type": "rule", "id": rule["id"], "content": rule.get("desc", "")})
    for concept in concepts:
        rows.append({"type": "concept", "id": concept["id"], "content": concept.get("desc", "")})

    return pd.DataFrame(rows)


def clean_dataframe_with_ai(raw_text: str, fallback_df: pd.DataFrame) -> pd.DataFrame:
    """Apply AI-powered cleaning to the parsed dataframe, falling back to original data."""

    cleaned_text = clean_text_with_ai(raw_text)
    try:
        return pd.read_csv(StringIO(cleaned_text))
    except Exception as exc:  # pragma: no cover - defensive logging for UI
        st.error(f"AI 교정 후 CSV 변환 실패: {exc}")
        return fallback_df


def merge_with_existing_csv(edited_df: pd.DataFrame) -> pd.DataFrame:
    """Merge edited dataframe with existing parsed CSV data, removing duplicates."""

    if os.path.exists(PARSED_CSV_PATH):
        old_df = pd.read_csv(PARSED_CSV_PATH)
        combined = pd.concat([old_df, edited_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["type", "id", "content"])
        return combined

    return edited_df


def render_db_preview_section() -> None:
    st.header("📦 DB 데이터 확인")

    if not st.button("DB에서 불러오기"):
        return

    db_df = load_csv_from_db("parsed_docs")
    if db_df.empty:
        st.warning("⚠️ DB에 데이터가 없습니다.")
        return

    st.subheader("📦 DB 불러오기 결과")
    st.dataframe(db_df, use_container_width=True)


def render_csv_summary_section() -> None:
    st.header("📝 CSV 요약")

    if not st.button("CSV 전체 요약"):
        return

    csv_text = build_combined_csv_text()
    if not csv_text:
        st.warning("CSV 데이터가 없습니다.")
        return

    try:
        summary, parts = summarize_long_csv(csv_text)
    except ValueError as exc:
        st.error(f"CSV 결합 오류: {exc}")
        return

    st.text_area("CSV 전체 요약 결과", summary, height=300)
    with st.expander("부분 요약 보기"):
        for part in parts:
            st.markdown(part)


def build_combined_csv_text() -> str:
    """Combine CSV files from the data directory into a single CSV text blob."""

    csv_dfs = load_csv_files(DATA_DIR)
    if not csv_dfs:
        return ""

    combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
    return combined_df.to_csv(index=False, encoding="utf-8-sig")


def render_keyword_summary_section() -> None:
    st.header("🔑 키워드별 문서 정리")
    keywords_input = st.text_input("키워드를 콤마(,)로 입력 (예: 재물, 혼인, 직장, 건강)")

    if not st.button("키워드별 정리 실행"):
        return

    csv_text = build_combined_csv_text()
    if not csv_text:
        st.warning("CSV 데이터가 없습니다.")
        return

    keywords = [keyword.strip() for keyword in keywords_input.split(",") if keyword.strip()]
    if not keywords:
        st.warning("키워드를 입력하세요.")
        return

    summary_by_kw = summarize_by_keywords(csv_text, keywords)
    st.text_area("키워드별 정리 결과", summary_by_kw, height=400)


def render_ai_consultation_section() -> None:
    st.header("💬 AI 상담")

    query = st.text_input("질문을 입력하세요:", key="user_query")
    search_mode = st.radio(
        "검색 모드 선택", ["벡터 검색", "하이브리드 검색"], horizontal=True
    )

    if not st.button("AI 응답 생성"):
        return

    if not query.strip():
        st.warning("질문을 입력하세요.")
        return

    if search_mode == "하이브리드 검색":
        docs = hybrid_search(query, db_dir=VECTOR_DB_DIR, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = generate_ai_response(f"{query}\n\n참고자료:\n{context}")
    else:
        answer = generate_ai_response(query)

    st.markdown(answer)


def render_database_build_section() -> None:
    st.header("🛠️ 데이터베이스 빌드")

    if not st.button("데이터베이스 빌드 실행"):
        return

    with st.spinner("문서를 파싱하고 DB/VectorDB를 빌드 중..."):
        vs = build_databases(data_dir=RAW_DOCS_DIR, db_dir=VECTOR_DB_DIR)

    if vs:
        st.success("✅ DB 및 VectorDB 빌드 완료")
    else:
        st.warning("⚠️ 빌드할 문서가 없습니다.")


def render_database_management_section() -> None:
    st.header("🗂️ DB 관리")

    if st.button("테이블 목록 보기"):
        tables = list_tables()
        if tables:
            st.write("📋 현재 DB 테이블 목록:")
            st.write(tables)
        else:
            st.info("DB에 테이블이 없습니다.")

    tables = list_tables()
    if not tables:
        return

    selected_table = st.selectbox("조회할 테이블 선택", tables, key="view_table")
    if st.button("테이블 불러오기"):
        df = load_csv_from_db(selected_table)
        if df.empty:
            st.warning("⚠️ 데이터가 없습니다.")
        else:
            st.dataframe(df, use_container_width=True)

    del_table = st.selectbox("삭제할 테이블 선택", tables, key="delete_table")
    if st.button("테이블 삭제"):
        drop_table(del_table)


def drop_table(table_name: str) -> None:
    """Safely drop a table from the SQLite database used by the app."""

    import sqlite3

    with sqlite3.connect("suri_m.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()

    st.success(f"🗑️ {table_name} 테이블 삭제 완료")


def main() -> None:
    configure_app()
    page_choice = st.sidebar.radio("📌 페이지 선택", ["문서 관리", "인물 프로필"])

    if page_choice == "문서 관리":
        render_document_management_page()
    else:
        profiles_page()


if __name__ == "__main__":
    main()
