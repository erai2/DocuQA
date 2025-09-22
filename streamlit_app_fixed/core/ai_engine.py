import os
import openai
import streamlit as st
from core.rag import search_vector_db
from core.settings_manager import load_settings

# 🔑 secrets.toml에서 API 키 불러오기
openai.api_key = st.secrets["OPENAI_API_KEY"]


def generate_ai_response(user_query: str):
    """문서 기반 Q&A"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_dir=st.secrets["VECTOR_DB_DIR"], k=3)
    context = "\n\n".join(
        [f"[출처:{d.metadata.get('source','unknown')}] {d.page_content}" for d in docs]
    )

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 수암명리 DocuQA 전문가야."},
            {"role": "user", "content": f"질문: {user_query}\n\n참고자료:\n{context}"},
        ],
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def ask_csv_ai(user_query: str):
    """CSV 데이터 기반 Q&A"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_dir=st.secrets["CSV_VECTOR_DB_DIR"], k=3)
    context = "\n\n".join([d.page_content for d in docs])

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 CSV 데이터를 분석하는 전문가야."},
            {"role": "user", "content": f"질문: {user_query}\n\n참고자료:\n{context}"},
        ],
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def summarize_with_ai(text: str, max_tokens: int = 500):
    """단일 텍스트 요약"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 문서를 간결하게 요약하는 전문가야."},
            {"role": "user", "content": f"다음 내용을 {max_tokens} 토큰 이내로 요약해줘:\n\n{text}"},
        ],
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]


def summarize_long_csv(csv_text: str, chunk_size: int = 2000, max_tokens: int = 500):
    """
    긴 CSV 텍스트를 chunk_size 단위로 나눠서 부분 요약 → 최종 종합 요약
    """
    chunks = []
    text_lines = csv_text.splitlines()

    # 🔹 CSV 텍스트를 일정 라인 단위로 나누기
    for i in range(0, len(text_lines), chunk_size):
        chunk = "\n".join(text_lines[i : i + chunk_size])
        chunks.append(chunk)

    part_summaries = []
    for idx, chunk in enumerate(chunks):
        try:
            part_summary = summarize_with_ai(chunk, max_tokens=max_tokens)
            part_summaries.append(f"▶️ Part {idx+1} 요약:\n{part_summary}")
        except Exception as e:
            part_summaries.append(f"⚠️ Part {idx+1} 요약 실패: {e}")

    # 🔹 부분 요약들을 종합 요약
    combined_text = "\n\n".join(part_summaries)
    final_summary = summarize_with_ai(combined_text, max_tokens=max_tokens)

    return final_summary, part_summaries
