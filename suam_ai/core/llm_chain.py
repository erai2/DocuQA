"""High level helper that turns rules + 질문 into an LLM answer."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate

try:  # pragma: no cover - optional dependency alias
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover
    from langchain.chat_models import ChatOpenAI  # type: ignore

from .analyzer import summarise_context
from .context_builder import build_context

__all__ = ["ask_suam"]

MODEL_NAME = "gpt-4o-mini"
load_dotenv()


@lru_cache(maxsize=1)
def _get_llm() -> ChatOpenAI:
    """Initialise the OpenAI chat model lazily."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요."
        )

    # The OpenAI client reads the environment variable automatically.
    return ChatOpenAI(model=MODEL_NAME, temperature=0)


def _build_prompt(context: Dict[str, Any]) -> ChatPromptTemplate:
    template = """
    당신은 수암명리 전문가입니다. 반드시 rules.json의 해석 순서와 규칙을 따르십시오.

    🔹 해석 순서:
    {해석순서}

    🔹 사건 조건:
    {사건조건}

    🔹 예외 규칙:
    {예외규칙}

    🔹 십성 변동 규칙:
    {십성변동}

    사용자의 질문: {질문}
    사주 데이터: {사주}

    👉 위 구조를 따라 단계별로 분석하고, 현실 사건 중심의 결론을 제시하세요.
    """

    return ChatPromptTemplate.from_template(template)


def ask_suam(user_question: str, saju_data: Optional[Dict[str, Any]] = None) -> str:
    """Return an expert style answer or a deterministic fallback summary."""

    context = build_context(user_question, saju_data)
    prompt = _build_prompt(context)

    def _format_prompt_value(value: Any) -> Any:
        if isinstance(value, list):
            return "\n".join(f"- {item}" for item in value)
        if isinstance(value, dict):
            return "\n".join(f"- {key}: {val}" for key, val in value.items())
        return value

    prompt_arguments = {
        key: _format_prompt_value(context.get(key))
        for key in ("해석순서", "사건조건", "예외규칙", "십성변동", "질문", "사주")
    }

    try:
        llm = _get_llm()
        messages = prompt.format_messages(**prompt_arguments)
        result = llm.invoke(messages)
        content = getattr(result, "content", str(result))
        if warning := context.get("rules_warning"):
            content += "\n\n⚠️ 규칙 파일 경고: " + warning
        return content
    except RuntimeError as exc:
        # Missing API key or rules file error.
        fallback = summarise_context(context)
        return f"⚠️ {exc}\n\n{fallback}"
    except Exception:  # pragma: no cover - defensive guard
        fallback = summarise_context(context)
        return (
            "⚠️ LLM 호출 중 오류가 발생했습니다. 콘솔 로그를 확인하세요.\n\n" + fallback
        )
