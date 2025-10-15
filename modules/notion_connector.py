"""Local stub mimicking Notion API interactions."""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Iterable

_DATA_DIR = Path(__file__).resolve().parent.parent / "streamlit_app_fixed" / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_NOTION_LOG_FILE = _DATA_DIR / "notion_log.jsonl"


def _load_secret(key: str) -> str | None:
    """Retrieve a secret from environment variables or .streamlit config."""

    value = os.getenv(key)
    if value:
        return value

    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib  # type: ignore
        with secrets_path.open("rb") as file:
            secrets = tomllib.load(file)
        return secrets.get(key)  # type: ignore[return-value]
    return None


def send_to_notion(text: str, tags: Iterable[str]) -> str:
    """Simulate sending data to Notion and return a pseudo page ID."""

    notion_token = _load_secret("NOTION_TOKEN")
    database_id = _load_secret("NOTION_DATABASE_ID")

    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "text": text,
        "tags": list(tags),
        "token_present": bool(notion_token),
        "database_present": bool(database_id),
    }

    with _NOTION_LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry["id"]
