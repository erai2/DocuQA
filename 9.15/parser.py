# parser.py
import os, re, glob, sqlite3, shutil
import pandas as pd
from typing import List, Dict, Any
from langchain_chroma import Chroma
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
# === 경로 설정 ===
INPUT_DIR = "data/raw_docs"
SQLITE_DB_PATH = "data/suri.db"
VECTOR_DB_DIR = "data/vector_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# === DB 초기화 ===
DDL = {
    "rules": "CREATE TABLE IF NOT EXISTS rules (rule_id TEXT PRIMARY KEY, title TEXT, content TEXT);",
    "cases": "CREATE TABLE IF NOT EXISTS cases (case_id TEXT PRIMARY KEY, title TEXT, content TEXT);",
    "concepts": "CREATE TABLE IF NOT EXISTS concepts (concept_id TEXT PRIMARY KEY, title TEXT, content TEXT);",
    "case_rules_link": "CREATE TABLE IF NOT EXISTS case_rules_link (case_id TEXT, rule_id TEXT, PRIMARY KEY (case_id, rule_id));"
}

def init_db():
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cur = conn.cursor()
        for sql in DDL.values():
            cur.execute(sql)
        conn.commit()
    print("✅ SQLite DB 초기화 완료")

# === 텍스트 → chunk 파싱 ===
def parse_text_to_chunks(text: str) -> List[Dict[str, Any]]:
    chunks = []
    pattern = r'(<사례.*?>.*?</사례>|<규칙.*?>.*?</규칙>|<개념.*?>.*?</개념>)'
    blocks = re.findall(pattern, text, re.DOTALL)

    for block in blocks:
        block_type = re.match(r'<(\w+)', block).group(1)
        id_match = re.search(r'id="([^"]+)"', block)
        if not id_match: continue
        chunk_id = id_match.group(1)
        content = re.sub(r'<[^>]+>', '', block).strip()
        title = content.split('\n', 1)[0].strip()
        chunks.append({"id": chunk_id, "type": block_type, "title": title, "content": content})
    return chunks

def extract_rule_links(case_content: str):
    match = re.search(r'\(규칙:\s*([^\)]+)\)', case_content)
    if match:
        return [r.strip() for r in match.group(1).split(',')]
    return []

# === chunk → DataFrame 변환 ===
def process_chunks_to_dataframes(chunks: List[Dict[str, Any]]):
    data = {"cases": [], "rules": [], "concepts": []}
    case_rule_links = []
    for ch in chunks:
        if ch["type"] == "사례":
            data["cases"].append({"case_id": ch["id"], "title": ch["title"], "content": ch["content"]})
            for r in extract_rule_links(ch["content"]):
                case_rule_links.append({"case_id": ch["id"], "rule_id": r})
        elif ch["type"] == "규칙":
            data["rules"].append({"rule_id": ch["id"], "title": ch["title"], "content": ch["content"]})
        elif ch["type"] == "개념":
            data["concepts"].append({"concept_id": ch["id"], "title": ch["title"], "content": ch["content"]})
    return {
        "cases": pd.DataFrame(data["cases"]),
        "rules": pd.DataFrame(data["rules"]),
        "concepts": pd.DataFrame(data["concepts"]),
        "case_rules_link": pd.DataFrame(case_rule_links),
    }

# === DB & VectorDB 구축 ===
def build_databases():
    all_chunks = []
    text_files = glob.glob(os.path.join(INPUT_DIR, "*.txt")) + glob.glob(os.path.join(INPUT_DIR, "*.md"))
    if not text_files:
        print(f"⚠️ '{INPUT_DIR}'에 처리할 텍스트 없음")
        return False

    for file_path in text_files:
        with open(file_path, "r", encoding="utf-8") as f:
            all_chunks.extend(parse_text_to_chunks(f.read()))

    # 중복 제거
    unique, seen = [], set()
    for ch in all_chunks:
        if ch["id"] not in seen:
            unique.append(ch); seen.add(ch["id"])

    dfs = process_chunks_to_dataframes(unique)

    init_db()
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        for name, df in dfs.items():
            if not df.empty:
                df.to_sql(name, conn, if_exists="replace", index=False)
    print("✅ SQLite DB 구축 완료")

    # Vector DB
    docs = []
    for name, df in dfs.items():
        if name == "case_rules_link" or df.empty: continue
        for _, row in df.iterrows():
            content = "\n".join([f"{k}: {v}" for k, v in row.items()])
            docs.append(Document(page_content=content, metadata={"source": name}))
    if docs:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        if os.path.exists(VECTOR_DB_DIR): shutil.rmtree(VECTOR_DB_DIR)
        Chroma.from_documents(docs, embeddings, persist_directory=VECTOR_DB_DIR)
        print("✅ Vector DB 구축 완료")

    return True
