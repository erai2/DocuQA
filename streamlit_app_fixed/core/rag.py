"""Utilities for building and querying the vector database backend."""

from __future__ import annotations

import os
from typing import List

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

__all__ = ["build_databases", "query_database", "search_vector_db"]


def build_databases(data_dir: str, db_dir: str) -> bool:
    """Create a FAISS vector store from text files in ``data_dir``."""

    if not os.path.exists(data_dir):
        print(f"⚠️ Data directory not found: {data_dir}")
        return False

    embeddings = OpenAIEmbeddings()
    texts: List[str] = []
    metadatas: List[dict] = []

    for fname in os.listdir(data_dir):
        if not fname.endswith((".txt", ".md")):
            continue

        fpath = os.path.join(data_dir, fname)
        with open(fpath, "r", encoding="utf-8") as file:
            content = file.read()

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
    """Return the ``k`` most similar documents from the persisted FAISS store."""

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(
        db_dir,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore.similarity_search(query, k=k)


def search_vector_db(query: str, db_dir: str, k: int = 5) -> List[Document]:
    """Backward compatible alias for :func:`query_database`.

    The Streamlit application historically imported ``search_vector_db`` from
    this module. During a refactor the helper was renamed to
    :func:`query_database`, which broke those imports and caused an
    :class:`ImportError` at application start-up. Reintroducing the function
    keeps the public API stable while delegating the actual work to
    :func:`query_database`.
    """

    return query_database(query=query, db_dir=db_dir, k=k)
