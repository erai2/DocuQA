import os
import sqlite3
import pandas as pd

DB_PATH = "suri_m.db"

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
            type TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

# =============================
# 2. CSV → DB 저장
# =============================
def insert_csv_to_db(df: pd.DataFrame, table_name: str = "parsed_docs") -> int:
    """CSV DataFrame을 DB에 저장 (덮어쓰기), 저장된 행 수 반환"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    row_count = len(df)
    conn.close()
    return row_count

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
# 4. DB 테이블 목록 조회
# =============================
def list_tables():
    """DB에 존재하는 모든 테이블 이름 반환"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables

# =============================
# 5. CSV 파일 관리
# =============================
def load_csv_files(folder: str) -> dict:
    """폴더 내 CSV 파일들을 {이름: DataFrame} 형태로 불러오기"""
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
