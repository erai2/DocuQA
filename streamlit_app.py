"""DocuQA Streamlit dashboard for managing legal documents and Q&A."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.chat_interface import refresh_search_engine, render_enhanced_chat
from modules.database import DB_PATH, PRIMARY_KEYS, delete_record, fetch_table, update_record
from modules.parser import BuildResult, build_databases, list_raw_documents

RAW_DOC_DIR = Path("data/raw_docs")
RAW_DOC_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="DocuQA", layout="wide")
st.title("🔮 DocuQA 문서 관리 & 질의응답")


def _save_uploaded_files(uploaded_files) -> None:
    for uploaded_file in uploaded_files:
        destination = RAW_DOC_DIR / uploaded_file.name
        destination.write_bytes(uploaded_file.getbuffer())


def _render_build_summary(result: BuildResult) -> None:
    if not result.counts:
        return
    summary = {table: int(count) for table, count in result.counts.items()}
    st.json(summary)


def _render_raw_document_overview() -> None:
    docs = list_raw_documents()
    if not docs:
        st.info("현재 raw_docs 폴더에 저장된 문서가 없습니다.")
        return

    data = []
    for path in docs:
        stats = path.stat()
        data.append(
            {
                "파일명": path.name,
                "크기(KB)": round(stats.st_size / 1024, 1),
                "수정일": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )
    st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)


def _render_document_editor(table: str) -> None:
    try:
        df = fetch_table(table)
    except ValueError as exc:
        st.error(str(exc))
        return

    if df.empty:
        st.info("선택한 테이블에 데이터가 없습니다.")
        return

    st.dataframe(df.drop(columns=["rowid"]), use_container_width=True, hide_index=True, height=400)

    pk_column = PRIMARY_KEYS.get(table)
    id_options = df[pk_column].tolist()
    selection = st.selectbox(
        "수정할 항목 선택",
        options=id_options,
        format_func=lambda value: f"{value} - {df.loc[df[pk_column] == value, 'title'].iat(0)}",
    )

    record = df.loc[df[pk_column] == selection].iloc[0]
    new_title = st.text_input("제목", value=record.get("title", ""))
    new_content = st.text_area("내용", value=record.get("content", ""), height=220)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 저장", key=f"save_{table}_{selection}"):
            update_record(table, selection, title=new_title, content=new_content)
            st.success("저장되었습니다.")
            st.experimental_rerun()
    with col2:
        if st.button("🗑️ 삭제", key=f"delete_{table}_{selection}"):
            delete_record(table, selection)
            st.warning("삭제되었습니다.")
            st.experimental_rerun()


tab_upload, tab_chat, tab_manage = st.tabs(["📂 문서 업로드 & DB", "💬 질의응답", "📊 데이터 관리"])

with tab_upload:
    st.subheader("문서 업로드 및 데이터베이스 재구축")

    uploaded_files = st.file_uploader(
        "문서를 업로드하세요 (txt/md)",
        type=["txt", "md"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        _save_uploaded_files(uploaded_files)
        st.success(f"{len(uploaded_files)}개의 문서를 저장했습니다. DB 재구축을 진행하세요.")

    rebuild = st.button("🛠 DB 재구축")
    if rebuild:
        result = build_databases()
        if result.success:
            st.success(result.message)
            _render_build_summary(result)
            refresh_search_engine()
        else:
            st.error(result.message)
        st.session_state["last_build_result"] = result
    elif "last_build_result" in st.session_state:
        st.caption(f"마지막 재구축: {st.session_state['last_build_result'].message}")

    st.markdown("### 저장된 원본 문서")
    _render_raw_document_overview()

with tab_chat:
    render_enhanced_chat()

with tab_manage:
    st.subheader("정제된 데이터 조회 및 수정")
    if not DB_PATH.exists():
        st.info("DB가 아직 생성되지 않았습니다. 먼저 문서를 업로드하고 재구축하세요.")
    else:
        options = list(PRIMARY_KEYS.keys())
        table = st.selectbox("조회할 테이블 선택", options=options)
        _render_document_editor(table)
