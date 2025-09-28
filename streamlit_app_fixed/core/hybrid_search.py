# core/hybrid_search.py
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
import os

def load_faiss_vectorstore(db_dir: str) -> FAISS:
    if not os.path.exists(db_dir):
        raise FileNotFoundError(f"Vector DB directory not found: {db_dir}")
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(db_dir, embeddings, allow_dangerous_deserialization=True)

def hybrid_search(query: str, db_dir: str, k: int = 5) -> List[Document]:
    vectorstore = load_faiss_vectorstore(db_dir)
    return vectorstore.similarity_search(query, k=k)
