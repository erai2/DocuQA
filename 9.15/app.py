import streamlit as st
import sqlite3, pandas as pd
import os
from parser import build_databases
from chat_interface import render_enhanced_chat

DB_PATH = "data/su갸.db"
RAW_DIR = "data/raw_docs"
os.makedirs(RAW_DIR, exist_ok=True)

st.set_page_config(page_title="suri 대시보드", layout="wide")

st.title("🔮 suri AI 대시보드")

# ================================
# 탭 구성: DB 관리 / 챗봇 / 문서 관리
# ================================
tab1, tab2, tab3 = st.tabs(["📂 DB 관리", "💬 챗봇", "📊 문서 관리 대시보드"])

# 📂 DB 관리 탭
with tab1:
    st.subheader("DB 관리")

    # 문서 업로드
    uploaded = st.file_uploader("문서 업로드 (txt/md)", type=["txt","md"])
    if uploaded:
        path = os.path.join(RAW_DIR, uploaded.name)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        st.success(f"✅ {uploaded.name} 저장 완료 (👉 DB 재구축 버튼을 눌러 반영하세요)")

    # DB 재구축
    if st.button("🛠 DB 재구축"):
        if build_databases():
            st.success("✅ DB & Vector DB 재구축 완료")
        else:
            st.error("⚠️ raw_docs 폴더에 처리할 파일이 없습니다.")

    # DB 미리보기
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        for table in ["cases", "rules", "concepts"]:
            st.markdown(f"### {table}")
            df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 20", conn)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"{table} 테이블이 비어 있습니다.")
        conn.close()
    else:
        st.info("DB가 아직 없습니다. 문서를 업로드 후 재구축하세요.")

# 💬 챗봇 탭
with tab2:
    st.subheader("AI 상담 챗봇")
    render_enhanced_chat()

# 📊 문서 관리 대시보드 탭
with tab3:
    st.subheader("정리된 문서 관리")

    if not os.path.exists(DB_PATH):
        st.warning("DB가 아직 없습니다. 문서를 업로드 후 DB를 재구축하세요.")
    else:
        conn = sqlite3.connect(DB_PATH)
        tables = ["cases", "rules", "concepts"]
        choice = st.selectbox("조회할 테이블", tables)
        df = pd.read_sql_query(f"SELECT rowid,* FROM {choice}", conn)

        # 데이터프레임 표시
        st.dataframe(df, use_container_width=True, height=400)

        # 행 수정/삭제
        if not df.empty:
            st.markdown("### ✏️ 선택 행 수정/삭제")
            rowid = st.number_input("Row ID 선택", min_value=1, max_value=len(df), step=1)
            record = df.iloc[rowid-1].to_dict()

            new_title = st.text_input("제목", value=record.get("title",""))
            new_content = st.text_area("내용", value=record.get("content",""))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("저장"):
                    conn.execute(f"UPDATE {choice} SET title=?, content=? WHERE rowid=?", 
                                 (new_title, new_content, rowid))
                    conn.commit()
                    st.success("✅ 저장 완료")
            with col2:
                if st.button("삭제"):
                    conn.execute(f"DELETE FROM {choice} WHERE rowid=?", (rowid,))
                    conn.commit()
                    st.warning("🗑️ 삭제 완료")

        conn.close()
