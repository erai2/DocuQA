import streamlit as st
import os
from parser import build_databases
from chat_interface import render_enhanced_chat

RAW_DIR = "data/raw_docs"
os.makedirs(RAW_DIR, exist_ok=True)

st.set_page_config(page_title="DocuQA 9.20", layout="wide")
st.title("🔮 DocuQA 9.20 (수암명리 DB 챗봇)")

if st.button("🛠 DB 재구축 (raw_docs 폴더 스캔)"):
    if build_databases():
        st.success("✅ DB & Vector DB 재구축 완료")
    else:
        st.error("⚠️ raw_docs 폴더에 처리할 파일이 없습니다.")

uploaded = st.file_uploader("📂 문서 업로드 (txt/md)", type=["txt","md"])
if uploaded:
    path = os.path.join(RAW_DIR, uploaded.name)
    with open(path, "wb") as f:
        f.write(uploaded.read())
    st.success(f"✅ {uploaded.name} 저장 완료 (👉 DB 재구축 버튼을 눌러 반영하세요)")

st.markdown("---")
render_enhanced_chat()
