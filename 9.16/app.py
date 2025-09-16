import streamlit as st
import os
from modules.parser import build_databases
from modules.chat_interface import render_enhanced_chat

RAW_DIR = "data/raw_docs"
st.set_page_config(page_title="DocuQA", layout="wide")
st.title("🔮 DocuQA (suri DB 챗봇)")

# DB rebuild button
if st.button("🛠 DB 재구축 (raw_docs 폴더 스캔)"):
    st.info("DB 및 벡터 DB 재구축을 시작합니다...")
    if build_databases():
        st.success("✅ DB & Vector DB 재구축 완료")
    else:
        st.error("⚠️ raw_docs 폴더에 처리할 파일이 없거나 오류가 발생했습니다.")

st.markdown("---")
render_enhanced_chat()