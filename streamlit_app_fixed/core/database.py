import os
import sqlite3
import pandas as pd

DB_PATH = "suri_m.db"

# =============================
# 1. DB 초기화
# =============================
def ensure_db():
    """SQLite DB 초기화 (parsed_docs 테이블 기본 구조 고정)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parsed_docs (
            type TEXT,
            id TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

# =============================
# 2. CSV → DB 저장
# =============================
def insert_csv_to_db(df: pd.DataFrame, table_name: str = "parsed_docs") -> int:
    """
    CSV DataFrame을 DB에 저장 (중복 제거 후 저장).
    content의 공백/줄바꿈 문제도 보정.
    """
    ensure_db()
    conn = sqlite3.connect(DB_PATH)

    # 🔹 content 컬럼이 있다면 문자열 전처리 (띄어쓰기/개행 깨짐 방지)
    if "content" in df.columns:
        df["content"] = (
            df["content"]
            .astype(str)
            .str.replace("\r\n", " ", regex=False)
            .str.replace("\n", " ", regex=False)
            .str.replace("  ", " ", regex=False)  # 중복 공백 정리
            .str.strip()
        )

    # 🔹 중복 제거
    if "id" in df.columns and "content" in df.columns:
        df = df.drop_duplicates(subset=["id", "content"])
    else:
        df = df.drop_duplicates()

    # 🔹 기존 데이터 불러오기
    try:
        old_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        if not old_df.empty:
            df = pd.concat([old_df, df], ignore_index=True).drop_duplicates()
    except Exception:
        pass  # 테이블 없으면 새로 생성

    # 🔹 저장 (덮어쓰기)
    df.to_sql(table_name, conn, if_exists="replace", index=False)

    conn.close()
    print(f"[DB 저장 완료] {table_name}: 총 {len(df)}행")
    return len(df)

# =============================
# 3. DB → DataFrame 불러오기
# =============================
def load_csv_from_db(table_name: str = "parsed_docs") -> pd.DataFrame:
    """DB 테이블을 DataFrame으로 불러오기"""
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        if "content" in df.columns:
            # 띄어쓰기 깨짐 보정
            df["content"] = (
                df["content"]
                .astype(str)
                .str.replace("\r\n", " ", regex=False)
                .str.replace("\n", " ", regex=False)
                .str.replace("  ", " ", regex=False)
                .str.strip()
            )
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

                if "content" in df.columns:
                    df["content"] = (
                        df["content"]
                        .astype(str)
                        .str.replace("\r\n", " ", regex=False)
                        .str.replace("\n", " ", regex=False)
                        .str.replace("  ", " ", regex=False)
                        .str.strip()
                    )

                name = os.path.splitext(file)[0]
                csv_dfs[name] = df
            except Exception as e:
                print(f"⚠️ {file} 불러오기 실패: {e}")
    return csv_dfs

# =============================
# 5. 테이블 목록 조회
# =============================
def list_tables() -> list:
    """DB에 존재하는 테이블 목록 반환"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    return tables
