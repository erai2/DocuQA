# core/ai_engine.py
import os
from typing import Union

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


def _build_preview_from_source(data_source: Union[str, pd.DataFrame]) -> str:
    """요약에 사용할 데이터 샘플 문자열 생성"""

    if isinstance(data_source, pd.DataFrame):
        if data_source.empty:
            return ""
        return data_source.head(20).to_string()

    if isinstance(data_source, str):
        potential_path = data_source.strip()
        if os.path.isfile(potential_path):
            try:
                df = pd.read_csv(potential_path)
            except Exception:
                # 경로로 처리했으나 실패 시 텍스트 그대로 활용
                return data_source
            if df.empty:
                return ""
            return df.head(20).to_string()
        # 파일 경로가 아니면 데이터 샘플 텍스트로 간주
        return data_source

    raise TypeError("data_source는 문자열 경로/텍스트 또는 pandas.DataFrame 이어야 합니다.")


def summarize_with_ai(data_source: Union[str, pd.DataFrame], save_path: str = None):
    """데이터 소스를 요약하여 반환"""

    preview = _build_preview_from_source(data_source)
    if not preview.strip():
        return "요약할 데이터가 없습니다. CSV를 먼저 준비해주세요."

    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")

    prompt = f"""
    다음은 데이터의 샘플입니다:

    {preview}

    이 데이터의 주요 패턴과 요약을 구조적으로 정리해주세요.
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
