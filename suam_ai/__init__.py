"""Suam AI - rules.json powered LLM assistant."""

from .core import ask_suam, build_context, generate_outline, load_rules, summarise_context

__all__ = [
    "ask_suam",
    "build_context",
    "generate_outline",
    "load_rules",
    "summarise_context",
]
