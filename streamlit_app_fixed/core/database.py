# core/database.py
import os
import sqlite3
import pandas as pd

# 항상 같은 DB를 쓰도록 경로 통일
DB_PATH = os.path.join("data", "suri_m.db")

def ensure_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.close()

def insert_csv_to_db(df: pd.DataFrame, table_name: str):
    """CSV DataFrame을 DB에 저장 (중복 제거)"""
    conn = sqlite3.connect(DB_PATH)
    # 기존 테이블이 있으면 DROP
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    conn.close()
    return len(df)

def load_csv_from_db(table_name: str):
    """DB에서 테이블을 불러오기"""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def list_tables():
    """현재 DB의 테이블 목록"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables
