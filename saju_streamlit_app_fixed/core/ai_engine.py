import os
import openai
from core.vector_engine import search_vector_db
from core.settings_manager import load_settings

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_ai_response(user_query, db_name="default_db"):
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(user_query, db_name=db_name, k=3)
    context = "\n\n".join([f"[출처:{d.metadata.get('source')}] {d.page_content}" for d in docs])

    prompt = f"""
    당신은 사주명리 전문가 상담사입니다.
    사용자의 질문에 답변할 때 반드시 아래 문서 기반 컨텍스트를 활용하세요.

    === 컨텍스트 ===
    {context}

    === 질문 ===
    {user_query}

    답변은 친절하고 구조적으로 설명하세요.
    """

    completion = openai.ChatCompletion.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "당신은 사주명리 전문가 상담사입니다."},
            {"role": "user", "content": prompt},
        ]
    )

    answer = completion.choices[0].message["content"]
    if docs:
        sources = ", ".join(set([d.metadata.get("source", "unknown") for d in docs]))
        answer += f"\n\n📌 참고자료: {sources}"

    return answer
