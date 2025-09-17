import streamlit as st
import os
import pandas as pd
import sqlite3

from core.database import ensure_db, insert_sample_data, load_csv_files
from core.ai_engine import generate_ai_response, summarize_with_ai

st.set_page_config(page_title="suri AI 분석 시스템", layout="wide")

st.title("📊 suri AI 분석 & 데이터 관리")

# --- DB 초기화 ---
if st.button("🗄 DB 초기화 (샘플 데이터 포함)"):
    ensure_db()
    insert_sample_data()
    st.success("DB 초기화 및 샘플 데이터 삽입 완료 ✅")

# --- CSV 관리 ---
st.header("📂 CSV 데이터 관리")
csv_dfs = load_csv_files("data")

if not csv_dfs:
    st.info("CSV 데이터가 없습니다. 먼저 업로드하세요.")
else:
    for name, df in csv_dfs.items():
        st.subheader(f"📑 {name}.csv")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button(f"{name}.csv 저장", key=f"save_{name}"):
            edited_df.to_csv(f"data/{name}.csv", index=False, encoding="utf-8-sig")
            st.success(f"{name}.csv 저장 완료 ✅")

# --- 문서 업로드 ---
st.header("📑 새 문서 업로드")
uploaded_files = st.file_uploader("txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        save_path = os.path.join("data/raw_docs", uploaded_file.name)
        os.makedirs("data/raw_docs", exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"{uploaded_file.name} 업로드 완료 ✅")

# --- AI Q&A ---
st.header("💬 AI 상담")
query = st.text_input("질문을 입력하세요:")
if st.button("AI 응답 생성"):
    if query.strip():
        answer = generate_ai_response(query)
        st.markdown(answer)
    else:
        st.warning("질문을 입력하세요.")

# --- AI 요약 기능 ---
st.header("📝 CSV 요약")
if st.button("CSV 전체 요약"):
    if not csv_dfs:
        st.warning("CSV 데이터가 없습니다.")
    else:
        combined_text = "\n".join([df.to_string() for df in csv_dfs.values()])
        summary = summarize_with_ai(combined_text)
        st.text_area("요약 결과", summary, height=300)

        if st.button("요약 결과 저장"):
            save_path = "data/summary.csv"
            pd.DataFrame([{"summary": summary}]).to_csv(save_path, index=False, encoding="utf-8-sig")
            st.success("요약 결과 저장 완료 ✅")
