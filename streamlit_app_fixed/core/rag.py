# core/rag.py
import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

def build_databases(data_dir: str, db_dir: str) -> bool:
    if not os.path.exists(data_dir):
        print(f"⚠️ Data directory not found: {data_dir}")
        return False
    embeddings = OpenAIEmbeddings()
    texts, metadatas = [], []
    for fname in os.listdir(data_dir):
        if not fname.endswith((".txt", ".md")):
            continue
        fpath = os.path.join(data_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        texts.append(content)
        metadatas.append({"source": fname})
    if not texts:
        print("⚠️ No documents to embed.")
        return False
    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    os.makedirs(db_dir, exist_ok=True)
    vectorstore.save_local(db_dir)
    return True

def query_database(query: str, db_dir: str, k: int = 5) -> List[Document]:
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(db_dir, embeddings, allow_dangerous_deserialization=True)
    return vectorstore.similarity_search(query, k=k)
