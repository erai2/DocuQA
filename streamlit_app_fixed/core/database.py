from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from typing import Dict, Optional

import pandas as pd

DB_PATH = "data/suri_mi.db"


def _ensure_data_dir(db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)


def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """SQLite 커넥션을 생성한다."""

    _ensure_data_dir(db_path)
    return sqlite3.connect(db_path)


def ensure_db(db_path: str = DB_PATH) -> None:
    """필요한 기본 테이블을 생성한다."""

    with closing(_get_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS basic_theory (
                id TEXT PRIMARY KEY,
                concept TEXT,
                definition TEXT,
                category TEXT,
                reference TEXT
            );
            CREATE TABLE IF NOT EXISTS terminology (
                id TEXT PRIMARY KEY,
                term TEXT,
                meaning TEXT,
                category TEXT,
                note TEXT
            );
            CREATE TABLE IF NOT EXISTS case_studies (
                id TEXT PRIMARY KEY,
                chart TEXT,
                gender TEXT,
                analysis TEXT,
                conclusion TEXT,
                tags TEXT
            );
            """
        )
        conn.commit()


def insert_sample_data(db_path: str = DB_PATH) -> None:
    """샘플 데이터를 기본 테이블에 삽입한다."""

    with closing(_get_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            INSERT OR IGNORE INTO basic_theory VALUES
            ('BT001', '세력(勢)', '木火勢 vs 金水勢 구도', '기본이론', 'Book2');
            INSERT OR IGNORE INTO terminology VALUES
            ('T001', '관인상생', '官이 印을 生하는 구조', '격국', '귀격');
            INSERT OR IGNORE INTO case_studies VALUES
            ('C001', '己甲丁癸 / 巳戌巳巳', '남', '木火勢가 癸水를 제압', '관직 성취', '적포구조');
            """
        )
        conn.commit()


def load_csv_files(folder: str = "data") -> Dict[str, pd.DataFrame]:
    """폴더 내 CSV 파일을 {파일명: DataFrame} 형태로 반환한다."""

    csv_dfs: Dict[str, pd.DataFrame] = {}
    if not os.path.exists(folder):
        return csv_dfs

    for file in os.listdir(folder):
        if not file.lower().endswith(".csv"):
            continue
        try:
            df = pd.read_csv(os.path.join(folder, file))
            name = os.path.splitext(file)[0]
            csv_dfs[name] = df
        except Exception as exc:  # pragma: no cover - 파일 손상 대응
            print(f"[ERROR] {file} 읽기 실패: {exc}")
    return csv_dfs


_INVALID_CHARS = re.compile(r"[^0-9a-zA-Z_]")


def _sanitize_table_name(table_name: str) -> str:
    sanitized = _INVALID_CHARS.sub("_", table_name.strip())
    if not sanitized:
        raise ValueError("테이블 이름이 비어있습니다.")
    if sanitized[0].isdigit():
        sanitized = f"t_{sanitized}"
    return sanitized


def insert_csv_to_db(
    df: pd.DataFrame,
    table_name: str,
    *,
    db_path: str = DB_PATH,
    if_exists: str = "replace",
) -> None:
    """DataFrame을 지정한 테이블로 저장한다."""

    if df is None:
        raise ValueError("저장할 DataFrame이 없습니다.")

    normalized = _sanitize_table_name(table_name)
    with closing(_get_connection(db_path)) as conn:
        df.to_sql(normalized, conn, if_exists=if_exists, index=False)
        conn.commit()


def load_csv_from_db(table_name: str, *, db_path: str = DB_PATH) -> Optional[pd.DataFrame]:
    """저장된 테이블을 DataFrame으로 반환한다."""

    normalized = _sanitize_table_name(table_name)
    with closing(_get_connection(db_path)) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (normalized,)
        )
        if cur.fetchone() is None:
            return None
        return pd.read_sql_query(f"SELECT * FROM {normalized}", conn)


def import_df_to_db(
    table_name: str,
    df: pd.DataFrame,
    *,
    db_path: str = DB_PATH,
    if_exists: str = "replace",
) -> None:
    """이전 호환성을 위해 제공되는 래퍼 함수."""

    insert_csv_to_db(df, table_name, db_path=db_path, if_exists=if_exists)
