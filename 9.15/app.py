import streamlit as st
import os
from modules.parser import parse_docx_to_db
from modules.chatbot import answer

st.set_page_config(page_title="suri DB chat", layout="wide")
st.title("🔮 suri DB chat")

# 1. 문서 업로드 → DB 저장
uploaded = st.file_uploader("📂 문서를 업로드하세요 (Book1~6, txt/docx)", type=["docx","txt"])
if uploaded:
    save_path = os.path.join("data/raw_docs", uploaded.name)
    with open(save_path, "wb") as f:
        f.write(uploaded.read())
    parse_docx_to_db(save_path)
    st.success(f"✅ {uploaded.name} → DB 반영 완료")

# 2. 사용자 질문
query = st.text_input("💬 질문을 입력하세요:")
if query:
    st.write(answer(query))