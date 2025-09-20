"""Streamlit UI for the Suam AI rules + LLM pipeline."""

from __future__ import annotations

import streamlit as st

from suam_ai.core.analyzer import summarise_context
from suam_ai.core.context_builder import build_context
from suam_ai.core.llm_chain import ask_suam

st.set_page_config(page_title="수암명리 AI 해석기", page_icon="📘", layout="centered")

st.title("📘 수암명리 AI 해석기 (룰셋 + LLM)")

with st.sidebar:
    st.header("실행 안내")
    st.markdown(
        """
        1. `.env` 파일에 `OPENAI_API_KEY`를 등록하세요.\\
        2. `data/rules.json`에 최신 룰셋을 반영하세요.\\
        3. 필요한 경우 FastAPI 서버(`main.py`)와 함께 사용할 수 있습니다.
        """
    )

col1, col2 = st.columns(2)
with col1:
    year = st.text_input("년주", placeholder="예: 戊辰")
    day = st.text_input("일주", placeholder="예: 己巳")
with col2:
    month = st.text_input("월주", placeholder="예: 辛酉")
    hour = st.text_input("시주", placeholder="예: 辛未")

gender = st.selectbox("성별", ["male", "female", "unknown"], index=2)
question = st.text_area("질문을 입력하세요", "이번 대운에서 혼인 응기가 있나요?")

if st.button("해석하기", type="primary"):
    saju_data = {
        "year": year.strip(),
        "month": month.strip(),
        "day": day.strip(),
        "hour": hour.strip(),
        "gender": gender,
    }

    with st.spinner("룰셋과 LLM을 호출하는 중입니다..."):
        answer = ask_suam(question, saju_data)

    st.markdown("---")
    st.subheader("AI 답변")
    st.markdown(answer)

    st.subheader("룰셋 개요")
    st.markdown(summarise_context(build_context(question, saju_data)))
else:
    st.info("사주 정보를 입력하고 ‘해석하기’를 눌러 결과를 확인하세요.")
