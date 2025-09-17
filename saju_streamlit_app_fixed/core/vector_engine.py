# core/vector_engine.py
# 역할: 업로드 문서들을 벡터DB(FAISS)에 저장하고 검색
# OpenAI 대신 HuggingFace 임베딩 사용 (무료/로컬)

import os
import pickle
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS

EMBEDDING_DIR = "data/embeddings"
os.makedirs(EMBEDDING_DIR, exist_ok=True)

# HuggingFace 로컬 임베딩 모델 (무료)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def build_vector_db_from_documents(documents, db_name="default_db"):
    """문서 리스트(Document 객체들)를 받아 벡터DB 생성"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    texts, metadatas = [], []
    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append({"source": doc.metadata.get("source", "unknown")})

    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)

    path = os.path.join(EMBEDDING_DIR, f"{db_name}.pkl")
    with open(path, "wb") as f:
        pickle.dump(vectorstore, f)

    return vectorstore

def load_vector_db(db_name="default_db"):
    """저장된 벡터DB 불러오기"""
    path = os.path.join(EMBEDDING_DIR, f"{db_name}.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

def search_vector_db(query, db_name="default_db", k=3):
    """질문(query)과 유사한 문서 검색"""
    db = load_vector_db(db_name)
    if db is None:
        return []
    return db.similarity_search(query, k=k)
