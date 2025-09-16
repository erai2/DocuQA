import streamlit as st
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from hybrid_search import HybridSearchEngine  # ✅

class ChatMessage:
    def __init__(self, role: str, content: str, sources: Optional[List[Dict]] = None):
        self.id = str(uuid.uuid4())
        self.role = role
        self.content = content
        self.sources = sources or []
        self.timestamp = datetime.now()

class EnhancedChatInterface:
    def __init__(self):
        self.search_engine = HybridSearchEngine()
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

    def render_chat_interface(self):
        st.subheader("💬 대화")
        for msg in st.session_state.chat_history:
            with st.chat_message(msg.role):
                st.write(msg.content)
                if msg.role == "assistant" and msg.sources:
                    with st.expander("📚 참고 자료"):
                        for i, src in enumerate(msg.sources):
                            st.markdown(f"**출처 {i+1}:** {src.get('filename','N/A')}")
                            st.caption(f"점수: {src.get('hybrid_score',0):.3f}")
                            st.write(src.get("content","")[:300] + "...")

        user_input = st.chat_input("질문을 입력하세요:")
        if user_input:
            self._process_input(user_input)

    def _process_input(self, text: str):
        st.session_state.chat_history.append(ChatMessage("user", text))
        with st.spinner("검색 중..."):
            results = self.search_engine.search(text, top_k=5)
            if results:
                answer = results[0]['content'][:500]
            else:
                answer = "❌ 관련 결과를 찾지 못했습니다."
            st.session_state.chat_history.append(ChatMessage("assistant", answer, results))
        st.rerun()

def render_enhanced_chat():
    EnhancedChatInterface().render_chat_interface()
