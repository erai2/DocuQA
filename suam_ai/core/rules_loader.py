"""Utilities for loading the project rule set."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

__all__ = ["RulesConfigError", "load_rules", "RULES_PATH"]

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "rules.json"


class RulesConfigError(RuntimeError):
    """Raised when the bundled ``rules.json`` file cannot be parsed."""


def _normalise_section(section: Any, *, default: Any) -> Any:
    """Return a JSON section with sane defaults.

    ``rules.json`` is authored manually, so a bit of defensive programming helps
    the runtime remain stable even if a section is missing or has a wrong type.
    """

    if section is None:
        return default

    if isinstance(default, list):
        if isinstance(section, list):
            return section
        if isinstance(section, dict):
            # Preserve keys while still returning a predictable structure.
            return [f"{key}: {value}" for key, value in section.items()]
        return [str(section)]

    if isinstance(default, dict):
        if isinstance(section, dict):
            return section
        raise RulesConfigError(
            "Expected a mapping in rules.json but received an incompatible value."
        )

    return section


@lru_cache(maxsize=1)
def load_rules(path: Path | str = RULES_PATH) -> Dict[str, Any]:
    """Load ``rules.json`` with validation and helpful error messages."""

    target = Path(path)
    if not target.exists():
        raise RulesConfigError(
            f"rules.json 파일을 찾을 수 없습니다: {target}. 경로를 확인하거나 최신 룰셋을 추가하세요."
        )

    try:
        with target.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive guard
        raise RulesConfigError(
            "rules.json 파일 형식이 올바르지 않습니다. JSON 문법 오류를 확인하세요."
        ) from exc

    payload = dict(payload or {})

    payload["analysis_order"] = _normalise_section(payload.get("analysis_order"), default=[])
    payload["event_conditions"] = _normalise_section(
        payload.get("event_conditions"), default=[]
    )
    payload["exceptions"] = _normalise_section(payload.get("exceptions"), default=[])
    payload["십성_변동"] = _normalise_section(payload.get("십성_변동"), default={})

    return payload
