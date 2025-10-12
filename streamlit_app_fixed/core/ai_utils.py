# core/ai_utils.py
import os
import logging
from functools import lru_cache
from typing import Optional, Tuple

import streamlit as st

from openai import OpenAI

try:  # 최신 OpenAI SDK (>=1.0)
    from openai import AuthenticationError, APIConnectionError, APIError
    from openai import RateLimitError as _RateLimitError
except ImportError:  # 구버전 호환
    from openai.error import (  # type: ignore[no-redef]
        AuthenticationError,
        APIConnectionError,
        OpenAIError as APIError,
        RateLimitError as _RateLimitError,
    )

RATE_LIMIT_ERRORS: Tuple[type, ...] = (_RateLimitError,) if "_RateLimitError" in locals() else tuple()

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


def _notify_streamlit(message: str, level: str = "warning", key: Optional[str] = None) -> None:
    """Streamlit UI에 중복 없이 경고 메시지를 띄운다."""

    if not hasattr(st, "session_state"):
        return

    if key:
        session_key = f"ai_utils_notice_{key}"
        if st.session_state.get(session_key):
            return
        st.session_state[session_key] = True

    display = getattr(st, level, None)
    if callable(display):
        try:
            display(message)
        except Exception:  # UI 경고 실패는 무시
            logging.debug("Streamlit 알림 표시 실패", exc_info=True)


def _handle_openai_error(exc: Exception, context: str) -> None:
    """OpenAI 호출 실패 시 사용자 친화적 메시지와 로그를 남긴다."""

    error_message = f"⚠️ {context} 실패: {exc}"
    logging.warning(error_message)

    if RATE_LIMIT_ERRORS and isinstance(exc, RATE_LIMIT_ERRORS):
        _notify_streamlit(
            "OpenAI API 사용량 한도가 초과되어 교정을 건너뜁니다. 관리자에게 문의해 주세요.",
            level="warning",
            key="rate_limit",
        )
        return

    if isinstance(exc, AuthenticationError):
        _notify_streamlit(
            "OpenAI API 키 인증에 실패했습니다. 환경 변수를 다시 확인해 주세요.",
            level="error",
            key="auth_error",
        )
        return

    if isinstance(exc, APIConnectionError):
        _notify_streamlit(
            "OpenAI API와 통신할 수 없습니다. 네트워크 상태를 확인하거나 잠시 후 다시 시도해 주세요.",
            level="warning",
            key="connection_error",
        )
        return

    if isinstance(exc, APIError):
        code = getattr(exc, "code", None)
        if code == "insufficient_quota":
            _notify_streamlit(
                "OpenAI 요금제가 소진되어 교정 기능을 중단합니다. 관리자가 결제를 갱신해야 합니다.",
                level="error",
                key="insufficient_quota",
            )
            return

    _notify_streamlit(
        "OpenAI 교정 기능에서 오류가 발생하여 원문을 그대로 사용합니다.",
        level="warning",
        key="generic_error",
    )

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
    except Exception as exc:  # pragma: no cover - 네트워크 오류 대응
        _handle_openai_error(exc, "clean_text_with_ai")
        return text  # 실패하면 원문 그대로 반환
