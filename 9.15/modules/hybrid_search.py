# modules/hybrid_search.py
import os, sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_community.vectorstores import Chroma   # ✅ 최신 방식
from langchain_community.embeddings import HuggingFaceEmbeddings

DB_PATH = "data/suri.db"
VECTOR_DB_DIR = "data/vector_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

class HybridSearchEngine:
    """
    하이브리드 검색 엔진:
    - TF-IDF (SQLite DB 기반)
    - Vector Search (Chroma + Embeddings)
    두 가지 결과를 합쳐 hybrid_score로 정렬.
    """

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        if os.path.exists(VECTOR_DB_DIR):
            self.vectorstore = Chroma(
                persist_directory=VECTOR_DB_DIR,
                embedding_function=self.embeddings
            )
        else:
            self.vectorstore = None

    def search(self, query: str, top_k: int = 5):
        results = []

        # === 1) SQLite DB (TF-IDF) ===
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query("SELECT rowid, * FROM cases", conn)
            conn.close()
            if not df.empty:
                vectorizer = TfidfVectorizer()
                tfidf = vectorizer.fit_transform(df['content'])
                query_vec = vectorizer.transform([query])
                scores = cosine_similarity(query_vec, tfidf).flatten()
                top_idx = scores.argsort()[::-1][:top_k]
                for i in top_idx:
                    results.append({
                        "filename": "cases",
                        "content": df.iloc[i]["content"],
                        "hybrid_score": float(scores[i])
                    })

        # === 2) Vector DB (Chroma) ===
        if self.vectorstore:
            docs = self.vectorstore.similarity_search_with_score(query, k=top_k)
            for doc, score in docs:
                results.append({
                    "filename": doc.metadata.get("source", "vector"),
                    "content": doc.page_content,
                    "hybrid_score": float(score)
                })

        # === 3) 점수순 정렬 ===
        results = sorted(results, key=lambda x: x["hybrid_score"], reverse=True)
        return results[:top_k]
