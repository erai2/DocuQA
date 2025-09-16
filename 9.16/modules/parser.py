import os
import re
import glob
import sqlite3
import shutil
import pandas as pd
from typing import List, Dict, Any
from langchain_chroma import Chroma  # Fixed import
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from modules.database import DDL, init_db, insert_doc_to_sql

INPUT_DIR = "data/raw_docs"
SQLITE_DB_PATH = "data/suri.db"
VECTOR_DB_DIR = "data/vector_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

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

def build_databases():
    all_chunks = []
    text_files = glob.glob(os.path.join(INPUT_DIR, "*.txt")) + glob.glob(os.path.join(INPUT_DIR, "*.md"))
    if not text_files:
        return False

    for file_path in text_files:
        with open(file_path, "r", encoding="utf-8") as f:
            all_chunks.extend(parse_text_to_chunks(f.read()))

    if not all_chunks:
        return False

    init_db()
    
    docs = []
    for chunk in all_chunks:
        insert_doc_to_sql(chunk['id'], chunk['type'], chunk['title'], chunk['content'])
        docs.append(Document(page_content=chunk['content'], metadata={"source": chunk['type']}))

    if docs:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        
        # Explicitly close any existing ChromaDB connections before removal
        if os.path.exists(VECTOR_DB_DIR):
            try:
                shutil.rmtree(VECTOR_DB_DIR)
            except PermissionError:
                print("PermissionError: Failed to remove directory. Please ensure no other process is using it.")
                return False

        Chroma.from_documents(docs, embeddings, persist_directory=VECTOR_DB_DIR)
        return True
    
    return False