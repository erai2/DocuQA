"""Database helpers for the DocuQA application."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

DB_PATH = Path("data/suri.db")

DDL: Dict[str, str] = {
    "cases": (
        "CREATE TABLE IF NOT EXISTS cases ("
        "case_id TEXT PRIMARY KEY, "
        "title TEXT, "
        "content TEXT"
        ")"
    ),
    "rules": (
        "CREATE TABLE IF NOT EXISTS rules ("
        "rule_id TEXT PRIMARY KEY, "
        "title TEXT, "
        "content TEXT"
        ")"
    ),
    "concepts": (
        "CREATE TABLE IF NOT EXISTS concepts ("
        "concept_id TEXT PRIMARY KEY, "
        "title TEXT, "
        "content TEXT"
        ")"
    ),
    "case_rules_link": (
        "CREATE TABLE IF NOT EXISTS case_rules_link ("
        "case_id TEXT, "
        "rule_id TEXT, "
        "PRIMARY KEY (case_id, rule_id)"
        ")"
    ),
}

PRIMARY_KEYS: Dict[str, str] = {
    "cases": "case_id",
    "rules": "rule_id",
    "concepts": "concept_id",
}


def ensure_data_folder() -> None:
    """Create the directory that stores the SQLite database if required."""
    os.makedirs(DB_PATH.parent, exist_ok=True)


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    """Context manager that yields a SQLite connection with foreign keys enabled."""
    ensure_data_folder()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Initialise the SQLite schema if it does not exist yet."""
    with get_connection() as conn:
        cur = conn.cursor()
        for ddl in DDL.values():
            cur.execute(ddl)
        conn.commit()


def write_tables(tables: Dict[str, pd.DataFrame]) -> None:
    """Persist the provided data frames into the SQLite database."""
    if not tables:
        return

    init_db()
    with get_connection() as conn:
        for table, df in tables.items():
            if df is None:
                continue
            df.to_sql(table, conn, if_exists="replace", index=False)


def fetch_table(table: str) -> pd.DataFrame:
    """Return the contents of a table including the SQLite rowid for editing."""
    if table not in DDL:
        raise ValueError(f"Unknown table: {table}")

    with get_connection() as conn:
        query = f"SELECT rowid, * FROM {table} ORDER BY rowid"
        return pd.read_sql_query(query, conn)


def update_record(table: str, identifier: str, *, title: str, content: str) -> None:
    """Update the title/content columns for a given record."""
    pk_column = PRIMARY_KEYS.get(table)
    if not pk_column:
        raise ValueError(f"Table '{table}' does not support editing")

    with get_connection() as conn:
        conn.execute(
            f"UPDATE {table} SET title = ?, content = ? WHERE {pk_column} = ?",
            (title, content, identifier),
        )
        conn.commit()


def delete_record(table: str, identifier: str) -> None:
    """Remove a record from the specified table."""
    pk_column = PRIMARY_KEYS.get(table)
    if not pk_column:
        raise ValueError(f"Table '{table}' does not support deletion")

    with get_connection() as conn:
        conn.execute(
            f"DELETE FROM {table} WHERE {pk_column} = ?",
            (identifier,),
        )
        conn.commit()


def list_available_tables() -> Iterable[str]:
    """Return the list of logical tables managed by the application."""
    return tuple(DDL.keys())

