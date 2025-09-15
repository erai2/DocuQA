import streamlit as st
import os
import sqlite3
import pandas as pd
from parser import build_databases   # 통합된 parser.py 불러오기

DB_PATH = "data/suam.db"
RAW_DIR = "data/raw_docs"
os.makedirs(RAW_DIR, exist_ok=True)

st.set_page_config(page_title="수암명리 DB 챗봇", layout="wide")
st.title("🔮 수암명리 DB 챗봇")

# 0. DB 재구축 버튼
if st.button("🛠 DB 재구축 (raw_docs 폴더 스캔)"):
    success = build_databases()
    if success:
        st.success("✅ DB & Vector DB 재구축 완료")
    else:
        st.error("⚠️ raw_docs 폴더에 처리할 파일이 없습니다.")

# 1. 문서 업로드 → raw_docs에 저장
uploaded = st.file_uploader("📂 문서를 업로드하세요 (txt/md)", type=["txt","md"])
if uploaded:
    save_path = os.path.join(RAW_DIR, uploaded.name)
    with open(save_path, "wb") as f:
        f.write(uploaded.read())
    st.success(f"✅ {uploaded.name} 저장 완료 (DB 재구축 버튼을 눌러 반영하세요)")

# 2. DB 내용 미리보기
st.subheader("📊 현재 DB 상태")
if os.path.exists(DB_PATH):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM cases LIMIT 20", conn
    )
    conn.close()
    st.dataframe(df)
else:
    st.info("아직 DB가 없습니다. 👉 '🛠 DB 재구축' 버튼을 눌러 생성하세요.")

# 3. 검색/챗봇은 hybrid_search 쪽 연결 가능
