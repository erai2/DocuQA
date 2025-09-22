import os
import openai
from core.rag import search_vector_db
from core.settings_manager import load_settings

# 🔑 OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_ai_response(user_query: str):
    """
    사용자의 질문을 받아서:
    1. 벡터DB에서 관련 문서 검색
    2. 검색 결과를 context로 묶음
    3. OpenAI GPT 모델에 전달하여 응답 생성
    """

    # 🔹 설정 불러오기
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    # 🔹 관련 문서 검색 (db_name → db_dir 수정됨)
    docs = search_vector_db(user_query, db_dir="data/vector_db", k=3)

    # 🔹 검색 결과를 context로 변환
    context = "\n\n".join(
        [f"[출처:{d.metadata.get('source', 'unknown')}] {d.page_content}" for d in docs]
    )

    # 🔹 프롬프트 구성
    prompt = f"""
    질문: {user_query}

    참고자료:
    {context}
    """

    # 🔹 OpenAI GPT 호출
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 수암명리 DocuQA 전문가야."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    return response["choices"][0]["message"]["content"]


def summarize_with_ai(text: str, max_tokens: int = 500):
    """
    주어진 텍스트를 OpenAI GPT 모델로 요약한다.
    """
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    # 🔹 프롬프트 구성
    prompt = f"다음 내용을 {max_tokens} 토큰 이내로 요약해줘:\n\n{text}"

    # 🔹 OpenAI GPT 호출
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "너는 문서를 간결하게 요약하는 전문가야."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )

    return response["choices"][0]["message"]["content"]
