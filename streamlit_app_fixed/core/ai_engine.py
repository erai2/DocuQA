# core/ai_engine.py
import os
import pandas as pd
from openai import OpenAI
from core.rag import search_vector_db
from core.settings_manager import load_settings

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_response(user_query, db_name="default_db"):
    """벡터DB 기반 답변 생성"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_name=db_name, k=3)
    context = "\n\n".join(
        [f"[출처:{d.metadata.get('source', 'unknown')}] {d.page_content}" for d in docs]
    )

    prompt = f"""
    당신은 사주명리 전문가 상담사입니다.
    반드시 아래 문서 기반 컨텍스트를 활용해 답변하세요.

    === 컨텍스트 ===
    {context}

    === 질문 ===
    {user_query}
    """

    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "당신은 사주명리 전문가 상담사입니다."},
            {"role": "user", "content": prompt},
        ],
    )

    answer = response.choices[0].message.content
    if docs:
        sources = ", ".join(set([d.metadata.get("source", "unknown") for d in docs]))
        answer += f"\n\n📌 참고자료: {sources}"

    return answer


def summarize_with_ai(csv_path: str, save_path: str = None):
    """CSV 파일 요약 → Streamlit에서 확인 및 저장 가능"""
    df = pd.read_csv(csv_path)
    preview = df.head(20).to_string()

    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")

    prompt = f"""
    다음은 데이터의 샘플입니다:

    {preview}

    이 CSV 데이터의 주요 패턴과 요약을 구조적으로 정리해주세요.
    """

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": "당신은 데이터 분석 및 요약 전문가입니다."},
            {"role": "user", "content": prompt},
        ],
    )

    summary = response.choices[0].message.content

    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(summary)

    return summary
