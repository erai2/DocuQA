"""Streamlit chat interface that leverages the hybrid search engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

import streamlit as st

from modules.hybrid_search import HybridSearchEngine


@dataclass
class ChatMessage:
    role: str
    content: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


def _get_search_engine() -> HybridSearchEngine:
    if "search_engine" not in st.session_state:
        st.session_state.search_engine = HybridSearchEngine()
    return st.session_state.search_engine


def _format_answer(results: List[Dict[str, str]]) -> str:
    if not results:
        return "❌ 관련 결과를 찾지 못했습니다. 다른 키워드로 다시 시도해 보세요."

    lines = ["🔎 검색된 자료 요약:"]
    for idx, item in enumerate(results[:3], start=1):
        title = item.get("title") or "제목 없음"
        snippet = (item.get("content") or "").strip().replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:180] + "..."
        source = item.get("source", "자료")
        lines.append(f"{idx}. **{title}** ({source}) - {snippet}")
    lines.append("\n더 자세한 내용은 아래 참고 자료를 확인하세요.")
    return "\n".join(lines)


def render_enhanced_chat() -> None:
    st.subheader("💬 AI 상담 챗봇")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history: List[ChatMessage] = []

    col1, col2 = st.columns([1, 0.2])
    with col1:
        st.markdown("질문을 입력하면 DB와 벡터 검색을 통해 관련 문서를 찾아 요약합니다.")
    with col2:
        if st.button("🧹 대화 초기화"):
            st.session_state.chat_history = []
            st.experimental_rerun()

    for message in st.session_state.chat_history:
        with st.chat_message(message.role):
            st.markdown(message.content)
            if message.role == "assistant" and message.sources:
                with st.expander("📚 참고 자료"):
                    for idx, src in enumerate(message.sources, start=1):
                        title = src.get("title") or "제목 없음"
                        snippet = (src.get("content") or "").strip()
                        if len(snippet) > 500:
                            snippet = snippet[:500] + "..."
                        st.markdown(f"**{idx}. {title}**")
                        st.write(snippet)
                        st.caption(src.get("source", "출처 미상"))

    user_input = st.chat_input("질문을 입력하세요")
    if not user_input:
        return

    st.session_state.chat_history.append(ChatMessage(role="user", content=user_input))
    engine = _get_search_engine()

    with st.spinner("지식을 검색하고 있습니다..."):
        results = engine.search(user_input, top_k=5)

    answer = _format_answer(results)
    st.session_state.chat_history.append(
        ChatMessage(role="assistant", content=answer, sources=results)
    )
    st.experimental_rerun()


def refresh_search_engine() -> None:
    """Force the cached search engine to reload the vector store."""
    engine = _get_search_engine()
    engine.reload_vectorstore()

