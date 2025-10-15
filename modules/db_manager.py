"""Persistence helpers for analysis results."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable

_DATA_DIR = Path(__file__).resolve().parent.parent / "streamlit_app_fixed" / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_JSON_FILE = _DATA_DIR / "analysis_results.json"
_SQLITE_FILE = _DATA_DIR / "analysis_results.db"


def _ensure_json_initialized() -> None:
    if not _JSON_FILE.exists():
        _JSON_FILE.write_text("[]", encoding="utf-8")


def save_to_json(structured: Dict[str, object]) -> None:
    """Append a structured record to the JSON log."""

    _ensure_json_initialized()
    with _JSON_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        data = []
    data.append(structured)
    with _JSON_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_to_sqlite(structured: Dict[str, object]) -> None:
    """Persist the structured data into a SQLite database."""

    connection = sqlite3.connect(_SQLITE_FILE)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT,
                original TEXT,
                summary TEXT,
                tags TEXT,
                confidence REAL,
                hash TEXT,
                notion_id TEXT
            )
            """
        )

        tags_value = structured.get("tags", [])
        if isinstance(tags_value, str) or not isinstance(tags_value, Iterable):
            tags_serialized = str(tags_value)
        else:
            tags_serialized = ",".join(str(tag) for tag in tags_value)

        cursor.execute(
            """
            INSERT INTO analysis (mode, original, summary, tags, confidence, hash, notion_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                structured.get("mode"),
                structured.get("original"),
                structured.get("summary"),
                tags_serialized,
                structured.get("confidence"),
                structured.get("hash"),
                structured.get("notion_id"),
            ),
        )
        connection.commit()
    finally:
        connection.close()
