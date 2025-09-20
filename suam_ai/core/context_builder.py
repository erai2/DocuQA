"""Build question-aware context dictionaries for the LLM chain."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .rules_loader import RulesConfigError, load_rules

__all__ = ["build_context"]


def _safe_get(payload: Dict[str, Any], key: str, default: Any) -> Any:
    value = payload.get(key, default)
    if isinstance(default, list) and not isinstance(value, list):
        return [value]
    if isinstance(default, dict) and not isinstance(value, dict):
        return default
    return value


def build_context(user_question: str, saju_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Combine user input with the shared rule set."""

    try:
        rules = load_rules()
        rule_error = None
    except RulesConfigError as exc:
        rules = {
            "analysis_order": [],
            "event_conditions": [],
            "exceptions": [],
            "십성_변동": {},
        }
        rule_error = str(exc)

    context = {
        "해석순서": _safe_get(rules, "analysis_order", []),
        "사건조건": _safe_get(rules, "event_conditions", []),
        "예외규칙": _safe_get(rules, "exceptions", []),
        "십성변동": _safe_get(rules, "십성_변동", {}),
        "질문": user_question,
        "사주": saju_data or {},
    }

    if rule_error:
        context["rules_warning"] = rule_error

    return context
