import sqlite3
import os
import pandas as pd

DB_PATH = "data/suam_myeongri.db"

def ensure_db():
    """DB 및 테이블 생성"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
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
    """)
    conn.commit()
    conn.close()

def insert_sample_data():
    """샘플 데이터 삽입"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    INSERT OR IGNORE INTO basic_theory VALUES
    ('BT001', '세력(勢)', '木火勢 vs 金水勢 구도', '기본이론', 'Book2');
    INSERT OR IGNORE INTO terminology VALUES
    ('T001', '관인상생', '官이 印을 生하는 구조', '격국', '귀격');
    INSERT OR IGNORE INTO case_studies VALUES
    ('C001', '己甲丁癸 / 巳戌巳巳', '남', '木火勢가 癸水를 제압', '관직 성취', '적포구조');
    """)
    conn.commit()
    conn.close()

def load_csv_files(folder="data"):
    """CSV를 {파일명: DataFrame} 형태로 불러오기"""
    csv_dfs = {}
    if not os.path.exists(folder):
        return csv_dfs
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(folder, file))
                name = os.path.splitext(file)[0]
                csv_dfs[name] = df
            except Exception as e:
                print(f"[ERROR] {file} 읽기 실패: {e}")
    return csv_dfs

def import_df_to_db(df: pd.DataFrame, table_name: str, db_path: str = DB_PATH):
    """
    DataFrame을 SQLite 테이블로 저장
    """
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print(f"[INFO] {table_name} 테이블에 데이터 삽입 완료 ✅")
