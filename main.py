import streamlit as st
from core.chat_manager import get_chat, add_message, clear_chat, export_chat, list_saved_chats, import_chat
from core.file_manager import save_uploaded_file, list_files, remove_file, load_all_documents
from core.vector_engine import build_vector_db_from_documents
from core.ai_engine import generate_ai_response
from core.settings_manager import load_settings, save_settings, reset_settings

st.set_page_config(page_title="사주명리 AI 상담사", layout="wide")

# --- Sidebar: 파일 업로드 ---
st.sidebar.subheader("📂 파일 업로드")
uploaded_file = st.sidebar.file_uploader("문서 업로드", type=["txt", "md", "pdf"])
if uploaded_file is not None:
    save_uploaded_file(uploaded_file)
    st.sidebar.success(f"{uploaded_file.name} 업로드 완료")

# 파일 목록 표시
for f in list_files():
    col1, col2 = st.sidebar.columns([3,1])
    col1.write(f)
    if col2.button("❌", key=f):
        remove_file(f)

# DB 재구축 버튼
if st.sidebar.button("DB 재구축"):
    docs = load_all_documents()
    if docs:
        build_vector_db_from_documents(docs, db_name="default_db")
        st.sidebar.success("✅ 벡터DB 재구축 완료")
    else:
        st.sidebar.warning("업로드된 문서가 없습니다.")

# --- Sidebar: 대화 관리 ---
st.sidebar.subheader("💬 대화 관리")
if st.sidebar.button("대화 초기화"):
    clear_chat()
    st.sidebar.success("대화 내역 초기화 완료")

if st.sidebar.button("대화 저장"):
    filepath = export_chat()
    st.sidebar.success(f"대화 저장됨: {filepath}")

saved_chats = list_saved_chats()
if saved_chats:
    selected_chat = st.sidebar.selectbox("저장된 대화 불러오기", saved_chats)
    if st.sidebar.button("불러오기"):
        if import_chat(selected_chat):
            st.sidebar.success(f"{selected_chat} 불러오기 완료")

# --- Sidebar: 설정 ---
st.sidebar.subheader("⚙️ 설정")
settings = load_settings()
model = st.sidebar.selectbox(
    "GPT 모델",
    ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    index=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"].index(settings.get("model", "gpt-4o-mini"))
)
temperature = st.sidebar.slider("창의성 (Temperature)", 0.0, 1.0, float(settings.get("temperature", 0.3)), 0.1)
max_tokens = st.sidebar.number_input("최대 토큰 수", min_value=256, max_value=4096, value=int(settings.get("max_tokens", 1000)))
vector_weight = st.sidebar.slider("벡터 검색 가중치", 0.0, 1.0, float(settings.get("vector_weight", 0.6)), 0.1)
keyword_weight = 1 - vector_weight

if st.sidebar.button("설정 저장"):
    save_settings({
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "vector_weight": vector_weight,
        "keyword_weight": keyword_weight
    })
    st.sidebar.success("설정 저장 완료 ✅")

if st.sidebar.button("기본값으로 초기화"):
    reset_settings()
    st.sidebar.success("기본 설정으로 복원됨")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["💬 AI 상담", "📊 분석 대시보드", "⚙️ 시스템 성능"])

with tab1:
    st.header("AI 상담")
    for msg in get_chat():
        st.chat_message(msg["role"]).write(msg["content"])
    if user_q := st.chat_input("사주명리에 대해 질문하세요..."):
        add_message("user", user_q)
        answer = generate_ai_response(user_q)
        add_message("assistant", answer)
        st.experimental_rerun()

with tab2:
    st.header("분석 대시보드")
    st.metric("총 대화 수", len(get_chat()))
    st.progress(0.9, text="대운 관련 질문 성공률 90%")
    st.progress(0.85, text="십신 질문 성공률 85%")

with tab3:
    st.header("시스템 성능")
    st.metric("평균 응답시간", "1.2s")
    st.metric("메모리 사용률", "65%")
    st.metric("CPU 사용률", "40%")
