import os
import openai
import streamlit as st
from core.rag import search_vector_db
from core.settings_manager import load_settings

# 🔑 secrets.toml 또는 환경변수에서 API 키 불러오기
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

# -------------------------
# 1. 문서 기반 Q&A
# -------------------------
def generate_ai_response(user_query: str):
    """문서 기반 Q&A"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_dir=st.secrets.get("VECTOR_DB_DIR", "data/vector_db"), k=3)
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

# -------------------------
# 2. CSV 기반 Q&A
# -------------------------
def ask_csv_ai(user_query: str):
    """CSV 데이터 기반 Q&A"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_dir=st.secrets.get("CSV_VECTOR_DB_DIR", "data/csv_vector_db"), k=3)
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

# -------------------------
# 3. 단일 텍스트 요약
# -------------------------
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

# -------------------------
# 4. 긴 CSV 요약 (chunk 나눔)
# -------------------------
def summarize_long_csv(csv_text: str, chunk_size: int = 2000, max_tokens: int = 500):
    """
    긴 CSV 텍스트를 chunk_size 단위로 나눠서 부분 요약 → 최종 종합 요약
    """
    text_lines = csv_text.splitlines()
    chunks = [ "\n".join(text_lines[i:i+chunk_size]) for i in range(0, len(text_lines), chunk_size) ]

    part_summaries = []
    for idx, chunk in enumerate(chunks):
        try:
            part_summary = summarize_with_ai(chunk, max_tokens=max_tokens)
            part_summaries.append(f"▶️ Part {idx+1} 요약:\n{part_summary}")
        except Exception as e:
            part_summaries.append(f"⚠️ Part {idx+1} 요약 실패: {e}")

    combined_text = "\n\n".join(part_summaries)
    final_summary = summarize_with_ai(combined_text, max_tokens=max_tokens)

    return final_summary, part_summaries

# -------------------------
# 5. 키워드별 정리
# -------------------------
def summarize_by_keywords(text: str, keywords: list[str], max_tokens: int = 700):
    """
    전체 문서를 읽고 주어진 키워드별로 정리/나열
    """
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    keyword_str = ", ".join(keywords)
    prompt = f"""
    다음 텍스트를 분석해서, 키워드({keyword_str})별로 내용을 정리해줘.
    각 키워드마다 관련된 내용을 요약하고, 없으면 '관련 없음'이라고 표시해줘.

    텍스트:
    {text}
    """

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 문서 요약과 분류 전문가야."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response["choices"][0]["message"]["content"]

# -------------------------
# 6. 텍스트 교정 (띄어쓰기, 오타)
# -------------------------
def clean_text_with_ai(text: str, max_tokens: int = 1000):
    """
    텍스트의 띄어쓰기, 맞춤법, 오타를 AI로 자동 교정.
    CSV 구조가 깨지지 않도록 주의.
    """
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = 0.0  # 교정은 창의성 불필요

    prompt = f"""
    다음 텍스트의 띄어쓰기와 맞춤법, 오타를 교정해줘.
    의미는 바꾸지 말고 표기만 수정해.
    CSV라면 구조가 깨지지 않도록 원래 열 구조를 유지해.

    -----
    {text}
    """

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 한국어 교정 전문가이자 데이터 정리 전문가야."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response["choices"][0]["message"]["content"]
