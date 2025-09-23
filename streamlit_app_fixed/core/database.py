# core/database.py
import os, sqlite3, pandas as pd

DB_PATH = os.path.join("data", "suri_m.db")

def ensure_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.close()

def insert_csv_to_db(df: pd.DataFrame, table_name: str = "parsed_docs"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")  # 항상 최신본으로 덮어쓰기
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    conn.close()
    return len(df)

def load_csv_from_db(table_name: str = "parsed_docs"):
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

def list_tables():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()
    return tables
