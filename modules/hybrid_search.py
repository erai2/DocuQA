"""Hybrid search that combines SQLite keyword search with vector similarity."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from modules.database import DB_PATH

VECTOR_DB_DIR = Path("data/vector_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

SQL_QUERIES: Dict[str, str] = {
    "cases": "SELECT case_id as identifier, title, content FROM cases WHERE title LIKE ? OR content LIKE ?",
    "rules": "SELECT rule_id as identifier, title, content FROM rules WHERE title LIKE ? OR content LIKE ?",
    "concepts": "SELECT concept_id as identifier, title, content FROM concepts WHERE title LIKE ? OR content LIKE ?",
}


class HybridSearchEngine:
    """Combine relational and vector search for richer answers."""

    def __init__(self) -> None:
        self.embeddings = None
        self.vectorstore = None
        self.reload_vectorstore()

    def reload_vectorstore(self) -> None:
        """(Re-)initialise the persisted Chroma vector store if it exists."""
        if VECTOR_DB_DIR.exists():
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            self.vectorstore = Chroma(
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embeddings,
            )
        else:
            self.embeddings = None
            self.vectorstore = None

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, str]]:
        query = query.strip()
        if not query:
            return []

        results: List[Dict[str, str]] = []
        results.extend(self._search_sqlite(query, limit=top_k))
        results.extend(self._search_vector(query, k=top_k))

        deduped: List[Dict[str, str]] = []
        seen = set()
        for item in results:
            key = (item.get("source"), item.get("title"), item.get("content"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped

    def _search_sqlite(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        if not DB_PATH.exists():
            return []

        pattern = f"%{query}%"
        matches: List[Dict[str, str]] = []
        with sqlite3.connect(DB_PATH) as conn:
            for table, sql in SQL_QUERIES.items():
                cur = conn.execute(sql + " LIMIT ?", (pattern, pattern, limit))
                rows = cur.fetchall()
                for identifier, title, content in rows:
                    matches.append(
                        {
                            "id": identifier,
                            "title": title,
                            "content": content,
                            "source": f"SQLite::{table}",
                        }
                    )
        return matches

    def _search_vector(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        if not self.vectorstore:
            return []

        docs = self.vectorstore.similarity_search(query, k=k)
        results: List[Dict[str, str]] = []
        for doc in docs:
            results.append(
                {
                    "id": doc.metadata.get("id"),
                    "title": doc.metadata.get("title", ""),
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Vector DB"),
                }
            )
        return results

