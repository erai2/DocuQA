import sqlite3
import os

DB_PATH = "data/suri.db"

DDL = {
    "concepts": "CREATE TABLE IF NOT EXISTS concepts (concept_id TEXT PRIMARY KEY, title TEXT, content TEXT);",
}

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        for sql in DDL.values():
            cur.execute(sql)
        conn.commit()

def insert_doc_to_sql(doc_id, doc_type, title, content):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        if doc_type in DDL:
            cur.execute(f"INSERT OR REPLACE INTO {doc_type} (concept_id, title, content) VALUES (?,?,?)",
                        (doc_id, title, content))
            conn.commit()