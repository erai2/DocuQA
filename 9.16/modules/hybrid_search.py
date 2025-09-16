import os
import sqlite3
import pandas as pd
from langchain_chroma import Chroma  # Fixed import
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "data/suri.db"
VECTOR_DB_DIR = "data/vector_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class HybridSearchEngine:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vectorstore = None
        if os.path.exists(VECTOR_DB_DIR):
            self.vectorstore = Chroma(
                persist_directory=VECTOR_DB_DIR,
                embedding_function=self.embeddings
            )
    
    def search(self, query: str, top_k: int = 5):
        results = []

        # === 1) SQLite DB search ===
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            # Example using a different table, adjust to your schema
            df = pd.read_sql_query("SELECT title, content FROM concepts WHERE content LIKE ?", conn, params=(f"%{query}%",))
            conn.close()
            for _, row in df.iterrows():
                results.append({
                    "title": row['title'],
                    "content": row['content'],
                    "source": "SQLite DB",
                })

        # === 2) Vector DB search ===
        if self.vectorstore:
            docs = self.vectorstore.similarity_search(query, k=top_k)
            for doc in docs:
                results.append({
                    "title": doc.metadata.get("title", "N/A"),
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Vector DB"),
                })

        return results