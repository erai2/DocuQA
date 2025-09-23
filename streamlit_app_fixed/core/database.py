import os
import sqlite3
import pandas as pd

DB_PATH = "suam_myeongri.db"

# =============================
# 1. DB 초기화
# =============================
def ensure_db():
    """SQLite DB와 기본 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parsed_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            col1 TEXT,
            col2 TEXT,
            col3 TEXT
        )
    """)
    conn.commit()
    conn.close()

# =============================
# 2. CSV → DB 저장
# =============================
def insert_csv_to_db(df: pd.DataFrame, table_name: str = "parsed_docs"):
    """CSV DataFrame을 DB에 저장 (기존 테이블은 덮어쓰기)"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()

# =============================
# 3. DB → DataFrame 불러오기
# =============================
def load_csv_from_db(table_name: str = "parsed_docs") -> pd.DataFrame:
    """DB 테이블을 DataFrame으로 불러오기"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df

# =============================
# 4. CSV 파일 관리
# =============================
def load_csv_files(folder: str) -> dict:
    """폴더 내 CSV 파일들을 DataFrame으로 불러오기"""
    csv_dfs = {}
    if not os.path.exists(folder):
        return csv_dfs

    for file in os.listdir(folder):
        if file.endswith(".csv"):
            path = os.path.join(folder, file)
            try:
                df = pd.read_csv(path)
                name = os.path.splitext(file)[0]
                csv_dfs[name] = df
            except Exception as e:
                print(f"⚠️ {file} 불러오기 실패: {e}")
    return csv_dfs
