# core/database.py
import os
import sqlite3
import pandas as pd

DB_PATH = "data/saju_data.db"
CSV_DIR = "data"

# --- SQLite 기본 연결 ---
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

# --- 테이블 초기화 ---
def init_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        desc TEXT,
        category TEXT,
        target TEXT,
        pattern TEXT,
        version INTEGER,
        last_updated TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        desc TEXT,
        category TEXT,
        version INTEGER,
        last_updated TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        gender TEXT,
        saju TEXT,
        details TEXT,
        category TEXT,
        last_updated TEXT
    )
    """)

    conn.commit()
    conn.close()

# --- CSV 관리 기능 ---
def load_csv_files():
    """data/ 폴더 내 모든 CSV 파일 경로 반환"""
    os.makedirs(CSV_DIR, exist_ok=True)
    return [os.path.join(CSV_DIR, f) for f in os.listdir(CSV_DIR) if f.endswith(".csv")]

def save_csv_file(file_path: str, df: pd.DataFrame):
    """편집된 DataFrame을 CSV 파일로 저장"""
    df.to_csv(file_path, index=False, encoding="utf-8-sig")

def load_csv_as_df(file_path: str) -> pd.DataFrame:
    """CSV 파일을 DataFrame으로 불러오기"""
    return pd.read_csv(file_path)

# --- SQLite ↔ CSV 변환 ---
def export_table_to_csv(table_name: str, out_path: str):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    conn.close()

def import_csv_to_table(csv_path: str, table_name: str):
    conn = get_connection()
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

# --- DataFrame → DB 저장 ---
def import_df_to_db(table_name: str, df: pd.DataFrame):
    """DataFrame을 SQLite 테이블에 추가 저장"""
    if df is None or df.empty:
        return
    conn = get_connection()
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()
