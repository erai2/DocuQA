import sqlite3, os

DB_PATH = "data/suri.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS docs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        category TEXT,
        content TEXT
    )
    """)
    conn.commit()
    conn.close()

def insert_doc(filename, category, content):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # 중복 방지 (같은 내용이 이미 있으면 패스)
    cur.execute("SELECT 1 FROM docs WHERE content=? LIMIT 1", (content,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO docs(filename, category, content) VALUES (?,?,?)",
            (filename, category, content)
        )
        conn.commit()
    conn.close()

def search_docs(keyword, top_k=5):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT category, content FROM docs WHERE content LIKE ? LIMIT ?",
                (f"%{keyword}%", top_k))
    rows = cur.fetchall()
    conn.close()
    return rows
