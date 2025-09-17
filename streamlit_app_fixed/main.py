# main.py
# Streamlit 앱 진입점
# 기능: 문서 업로드 → 자동 파싱/DB 저장 → 벡터DB 검색 → AI 응답/요약 → CSV 관리

import streamlit as st
import os

from core.parsing import parse_and_store_documents
from core.ai_engine import generate_ai_response, summarize_with_ai
from core.rag import build_databases, search_vector_db
from core.database import load_csv_files, import_df_to_db
from core.settings_manager import load_settings

# --- 초기 환경설정 ---
st.set_page_config(page_title="QnA", layout="wide")
DATA_DIR = "data/raw_docs"
DB_NAME = "default_db"

# --- 사이드바 메뉴 ---
menu = st.sidebar.radio("메뉴 선택", ["문서 업로드", "DB 관리", "QnA", "CSV 요약"])

# --- 문서 업로드 ---
if menu == "문서 업로드":
    st.header("📤 문서 업로드 및 DB 저장")

    uploaded_files = st.file_uploader("문서를 업로드하세요", type=["txt", "md"], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            file_path = os.path.join(DATA_DIR, file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())

        parse_and_store_documents(DATA_DIR)
        build_databases(DB_NAME)
        st.success("문서가 저장되고 벡터DB가 갱신되었습니다 ✅")

# --- DB 관리 ---
elif menu == "DB 관리":
    st.header("🗂 데이터베이스 관리")

    csv_dfs = load_csv_files()
    if not csv_dfs:
        st.info("CSV 데이터가 없습니다. 먼저 문서를 업로드하세요.")
    else:
        for name, df in csv_dfs.items():
            st.subheader(f"📑 {name}.csv")
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button(f"{name}.csv 저장"):
                import_df_to_db(edited_df, table_name=name)
                edited_df.to_csv(f"data/{name}.csv", index=False)
                st.success(f"{name}.csv 저장 완료 ✅")

# --- AI 상담 ---
elif menu == "QnA":
    st.header("💬 AI 기반 상담")

    query = st.text_area("질문을 입력하세요:")
    if st.button("질문하기") and query:
        answer = generate_ai_response(query, db_name=DB_NAME)
        st.markdown("### 🔎 답변")
        st.write(answer)

# --- CSV 요약 ---
elif menu == "CSV 요약":
    st.header("📊 CSV → 요약 → 저장")

    csv_dfs = load_csv_files()
    if not csv_dfs:
        st.info("CSV 데이터가 없습니다.")
    else:
        selected_file = st.selectbox("요약할 CSV 선택", list(csv_dfs.keys()))
        df = csv_dfs[selected_file]

        st.dataframe(df)

        if st.button("AI 요약 생성"):
            summary = summarize_with_ai(df.to_csv(index=False))
            st.text_area("요약 결과", summary, height=200)

            if st.button("요약 CSV 저장"):
                summary_path = f"data/{selected_file}_summary.csv"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write("summary\n")
                    f.write(summary.replace("\n", " ") + "\n")
                st.success(f"요약 CSV 저장 완료: {summary_path}")
