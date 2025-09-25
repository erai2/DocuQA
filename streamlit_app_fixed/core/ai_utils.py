# core/ai_utils.py
import os
import logging
from openai import OpenAI
from functools import lru_cache
import streamlit as st

# -------------------------
# 내부 유틸
# -------------------------
def _get_secret(name: str):
    """Streamlit secrets에서 값을 안전하게 가져온다."""
    secrets_obj = getattr(st, "secrets", None)
    if secrets_obj is not None:
        getter = getattr(secrets_obj, "get", None)
        if callable(getter):
            value = getter(name)
            if value:
                return value
    return None

def _load_api_key() -> str:
    """Streamlit secrets 또는 환경 변수에서 OpenAI API 키를 읽어온다."""
    secret_key = _get_secret("OPENAI_API_KEY")
    if secret_key:
        return secret_key
    return os.getenv("OPENAI_API_KEY")

@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    """OpenAI 클라이언트를 초기화한다."""
    api_key = _load_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenAI API 키가 설정되어 있지 않습니다. "
            "환경 변수 OPENAI_API_KEY 또는 .streamlit/secrets.toml을 확인해주세요."
        )
    try:
        return OpenAI(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"OpenAI 클라이언트 초기화 실패: {exc}") from exc

# -------------------------
# 텍스트 교정 함수
# -------------------------
def clean_text_with_ai(text: str, max_tokens: int = 1000, model: str = "gpt-4o-mini") -> str:
    """
    텍스트의 띄어쓰기, 맞춤법, 오타를 AI로 자동 교정
    - 의미는 바꾸지 않고 표기만 수정
    - CSV 구조 깨지지 않게 유지
    """
    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "너는 한국어 교정 전문가이자 데이터 정리 전문가야."},
                {"role": "user", "content": f"""
                다음 텍스트의 띄어쓰기와 맞춤법, 오타를 교정해줘.
                의미는 바꾸지 말고 표기만 수정해.
                CSV라면 구조가 깨지지 않도록 원래 열 구조를 유지해.

                -----
                {text}
                """},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logging.warning(f"⚠️ clean_text_with_ai 실패: {exc}")
        return text  # 실패하면 원문 그대로 반환
