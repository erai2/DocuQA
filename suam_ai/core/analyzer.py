"""Light-weight rule based analyser used before invoking the LLM."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

__all__ = ["generate_outline", "summarise_context"]


def _format_list(items: Iterable[Any]) -> str:
    text = "\n".join(f"- {item}" for item in items if item)
    return text or "- (등록된 룰이 없습니다)"


def generate_outline(context: Dict[str, Any]) -> str:
    """Return a deterministic outline using the bundled rules."""

    steps: List[str] = []

    steps.append("🔹 해석 순서:\n" + _format_list(context.get("해석순서", [])))
    steps.append("🔹 사건 조건:\n" + _format_list(context.get("사건조건", [])))
    steps.append("🔹 예외 규칙:\n" + _format_list(context.get("예외규칙", [])))

    변동 = context.get("십성변동") or {}
    if 변동:
        변동_lines = "\n".join(f"- {key}: {value}" for key, value in 변동.items())
    else:
        변동_lines = "- (등록된 변동 규칙이 없습니다)"
    steps.append("🔹 십성 변동 규칙:\n" + 변동_lines)

    if warning := context.get("rules_warning"):
        steps.append("⚠️ 룰셋 로드 경고: " + warning)

    return "\n\n".join(steps)


def summarise_context(context: Dict[str, Any]) -> str:
    """Create a Korean summary that can be shown without LLM access."""

    user = context.get("질문") or "질문이 입력되지 않았습니다."
    saju = context.get("사주") or {}

    saju_lines = "\n".join(f"- {key}: {value}" for key, value in saju.items() if value)
    if not saju_lines:
        saju_lines = "- (사주 데이터가 입력되지 않았습니다)"

    template = (
        "사용자 질문 요약:\n{question}\n\n"
        "입력된 사주 정보:\n{saju}\n\n"
        "룰셋 개요:\n{outline}"
    )

    return template.format(question=user, saju=saju_lines, outline=generate_outline(context))
