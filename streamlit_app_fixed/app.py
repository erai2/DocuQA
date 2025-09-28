"""Streamlit entrypoint for the Suri Q&AI application (최종 실행본)."""

import os
from io import StringIO
from typing import Dict, Iterable, List
import pandas as pd
import streamlit as st

from core.ai_engine import generate_ai_response, summarize_by_keywords, summarize_long_csv
from core.hybrid_search import hybrid_search
from core.rag import build_databases


DATA_DIR = "data"
RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_docs")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
PARSED_CSV_PATH = os.path.join(DATA_DIR, "parsed_docs.csv")


def configure_app():
    st.set_page_config(page_title="Suri Q&AI", layout="wide")
    st.title("📊 Suri Q&AI")
    ensure_directories([DATA_DIR, RAW_DOCS_DIR, VECTOR_DB_DIR])


def ensure_directories(paths: Iterable[str]):
    for path in paths:
        os.makedirs(path, exist_ok=True)


# ----------------------------
# 문서 업로드
# ----------------------------
def render_upload_section():
    st.header("📑 문서 업로드 및 파싱")
    uploaded_files = st.file_uploader("txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True)
    if not uploaded_files:
        return

    for uploaded_file in uploaded_files:
        content = uploaded_file.read().decode("utf-8")
        st.subheader(f"📄 {uploaded_file.name}")
        st.text_area("파일 내용 미리보기", content[:1000], height=200)

        save_path = os.path.join(RAW_DOCS_DIR, uploaded_file.name)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(content)
        st.success(f"✅ 저장 완료: {save_path}")


# ----------------------------
# DB 빌드
# ----------------------------
def render_db_build():
    st.header("🛠️ 데이터베이스 빌드")
    if st.button("DB 빌드 실행"):
        ok = build_databases(RAW_DOCS_DIR, VECTOR_DB_DIR)
        if ok:
            st.success("✅ Vector DB 빌드 완료")
        else:
            st.warning("⚠️ 빌드할 문서가 없습니다.")


# ----------------------------
# CSV 요약
# ----------------------------
def render_summary():
    st.header("📝 CSV 요약")
    if not os.path.exists(PARSED_CSV_PATH):
        st.warning("CSV 파일이 없습니다.")
        return

    csv_text = open(PARSED_CSV_PATH, "r", encoding="utf-8").read()
    if st.button("CSV 전체 요약"):
        summary, parts = summarize_long_csv(csv_text)
        st.text_area("요약 결과", summary, height=300)


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
# Main
# ----------------------------
def main():
    configure_app()
    choice = st.sidebar.radio("페이지 선택", ["문서 업로드", "DB 빌드", "요약", "상담"])
    if choice == "문서 업로드":
        render_upload_section()
    elif choice == "DB 빌드":
        render_db_build()
    elif choice == "요약":
        render_summary()
    elif choice == "상담":
        render_ai_consultation()


if __name__ == "__main__":
    main()
