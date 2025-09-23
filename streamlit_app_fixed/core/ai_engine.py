import logging
import os
from functools import lru_cache
from typing import Dict, List, Optional

import streamlit as st
from openai import OpenAI

from core.rag import search_vector_db
from core.settings_manager import load_settings


def _get_secret(name: str) -> Optional[str]:
    """Streamlit secrets에서 값을 안전하게 가져온다."""

    secrets_obj = getattr(st, "secrets", None)
    if secrets_obj is not None:
        getter = getattr(secrets_obj, "get", None)
        if callable(getter):
            value = getter(name)
            if value:
                return value
    return None


def _load_api_key() -> Optional[str]:
    """Streamlit secrets 또는 환경 변수에서 OpenAI API 키를 읽어온다."""

    secret_key = _get_secret("OPENAI_API_KEY")
    if secret_key:
        return secret_key
    return os.getenv("OPENAI_API_KEY")


def _get_path_setting(env_name: str, default: str) -> str:
    """경로 설정 값을 secrets → 환경 변수 → 기본값 순으로 조회한다."""

    secret_value = _get_secret(env_name)
    if secret_value:
        return secret_value
    env_value = os.getenv(env_name)
    if env_value:
        return env_value
    return default


@lru_cache(maxsize=1)
def _get_openai_client() -> OpenAI:
    """OpenAI 클라이언트를 초기화한다.

    키가 존재하지 않을 경우 RuntimeError를 발생시켜 호출 측에서 사용자에게
    친절한 메시지를 전달할 수 있도록 한다.
    """

    api_key = _load_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenAI API 키가 설정되어 있지 않습니다. 환경 변수 OPENAI_API_KEY 또는 "
            ".streamlit/secrets.toml을 확인해주세요."
        )
    try:
        return OpenAI(api_key=api_key)
    except Exception as exc:  # pragma: no cover - 안전 장치
        raise RuntimeError(f"OpenAI 클라이언트 초기화에 실패했습니다: {exc}") from exc


def _chat_completion(
    messages: List[Dict[str, str]], *, model: str, temperature: float, **kwargs
) -> str:
    """OpenAI ChatCompletion 호출을 공통 처리한다."""

    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            **kwargs,
        )
        return response.choices[0].message.content
    except RuntimeError as exc:
        logging.warning("OpenAI API 키 오류: %s", exc)
        return f"⚠️ {exc}"
    except Exception as exc:  # pragma: no cover - 외부 API 예외 대비
        logging.exception("OpenAI 호출 중 오류: %s", exc)
        return f"⚠️ OpenAI 호출 중 오류가 발생했습니다: {exc}"

# -------------------------
# 1. 문서 기반 Q&A
# -------------------------
def generate_ai_response(user_query: str) -> str:
    """문서 기반 Q&A"""

    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(
        user_query,
        db_dir=_get_path_setting("VECTOR_DB_DIR", "data/vector_db"),
        k=3,
    )
    context = "\n\n".join(
        [f"[출처:{d.metadata.get('source','unknown')}] {d.page_content}" for d in docs]
    )

    return _chat_completion(
        [
            {"role": "system", "content": "너는 수암명리 DocuQA 전문가야."},
            {"role": "user", "content": f"질문: {user_query}\n\n참고자료:\n{context}"},
        ],
        model=model,
        temperature=temperature,
    )

# -------------------------
# 2. CSV 기반 Q&A
# -------------------------
def ask_csv_ai(user_query: str) -> str:
    """CSV 데이터 기반 Q&A"""

    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    docs = search_vector_db(
        user_query,
        db_dir=_get_path_setting("CSV_VECTOR_DB_DIR", "data/csv_vector_db"),
        k=3,
    )
    context = "\n\n".join([d.page_content for d in docs])

    return _chat_completion(
        [
            {"role": "system", "content": "너는 CSV 데이터를 분석하는 전문가야."},
            {"role": "user", "content": f"질문: {user_query}\n\n참고자료:\n{context}"},
        ],
        model=model,
        temperature=temperature,
    )

# -------------------------
# 3. 단일 텍스트 요약
# -------------------------
def summarize_with_ai(text: str, max_tokens: int = 500) -> str:
    """단일 텍스트 요약"""

    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")
    temperature = float(settings.get("temperature", 0.3))

    return _chat_completion(
        [
            {"role": "system", "content": "너는 문서를 간결하게 요약하는 전문가야."},
            {"role": "user", "content": f"다음 내용을 {max_tokens} 토큰 이내로 요약해줘:\n\n{text}"},
        ],
        model=model,
        temperature=temperature,
    )

# -------------------------
# 4. 긴 CSV 요약 (chunk 나눔)
# -------------------------
def summarize_long_csv(csv_text: str, chunk_size: int = 2000, max_tokens: int = 500):
    """긴 CSV 텍스트를 chunk 단위로 나눠서 부분 요약 → 최종 종합 요약"""
    text_lines = csv_text.splitlines()
    chunks = ["\n".join(text_lines[i:i+chunk_size]) for i in range(0, len(text_lines), chunk_size)]

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
def summarize_by_keywords(text: str, keywords: List[str], max_tokens: int = 700) -> str:
    """전체 문서를 키워드별로 정리"""
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

    return _chat_completion(
        [
            {"role": "system", "content": "너는 문서 요약과 분류 전문가야."},
            {"role": "user", "content": prompt},
        ],
        model=model,
        temperature=temperature,
    )

# -------------------------
# 6. 텍스트 교정 (띄어쓰기, 오타)
# -------------------------
def clean_text_with_ai(text: str, max_tokens: int = 1000) -> str:
    """텍스트의 띄어쓰기, 맞춤법, 오타를 AI로 자동 교정"""
    settings = load_settings()
    model = settings.get("model", "gpt-4o-mini")

    prompt = f"""
    다음 텍스트의 띄어쓰기와 맞춤법, 오타를 교정해줘.
    의미는 바꾸지 말고 표기만 수정해.
    CSV라면 구조가 깨지지 않도록 원래 열 구조를 유지해.

    -----
    {text}
    """

    return _chat_completion(
        [
            {"role": "system", "content": "너는 한국어 교정 전문가이자 데이터 정리 전문가야."},
            {"role": "user", "content": prompt},
        ],
        model=model,
        temperature=0.0,
        max_tokens=max_tokens,
    )
