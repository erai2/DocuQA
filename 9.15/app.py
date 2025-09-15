import streamlit as st
import os
import sqlite3
import pandas as pd
from modules.parser import parse_docx_to_db
from modules.chatbot import answer

st.set_page_config(page_title="suri DB chat", layout="wide")
st.title("🔮 suri DB chat")

DB_PATH = "data/suam.db"

# 1. 문서 업로드 → DB 저장
uploaded = st.file_uploader("📂 문서를 업로드하세요 (Book1~6, txt/docx)", type=["docx","txt"])
if uploaded:
    save_path = os.path.join("data/raw_docs", uploaded.name)
    with open(save_path, "wb") as f:
        f.write(uploaded.read())
    parse_docx_to_db(save_path)
    st.success(f"✅ {uploaded.name} → DB 반영 완료")

# 2. DB 내용 미리보기
st.subheader("📊 현재 DB 상태")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT id, filename, category, substr(content,1,150) as preview FROM docs ORDER BY id DESC",
        conn
    )
    conn.close()
    st.dataframe(df)
else:
    st.info("아직 DB가 생성되지 않았습니다.")

# 3. 챗봇 질의응답
st.subheader("💬 질문하기")
query = st.text_input("궁금한 점을 입력하세요:")
if query:
    st.write(answer(query))
