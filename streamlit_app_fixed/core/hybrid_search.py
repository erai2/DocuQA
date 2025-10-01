"""Hybrid search utilities combining vector and keyword retrieval."""

from __future__ import annotations

import re
from typing import List, Sequence

import pandas as pd

from core.database import load_csv_from_db
from core.rag import search_vector_db

try:  # langchain 0.1+
    from langchain.schema import Document
except ImportError:  # pragma: no cover - compatibility for older langchain
    try:
        from langchain.docstore.document import Document  # type: ignore
    except ImportError:  # pragma: no cover - fallback when langchain isn't installed
        from dataclasses import dataclass, field

        @dataclass
        class Document:  # type: ignore[override]
            """Minimal fallback Document structure used when langchain is unavailable."""

            page_content: str
            metadata: dict = field(default_factory=dict)


DEFAULT_TABLE = "parsed_docs"


def _iter_keyword_matches(query: str, limit: int) -> List[Document]:
    """Yield keyword-based matches from the structured SQLite table."""

    if not query.strip():
        return []

    df = load_csv_from_db(DEFAULT_TABLE)
    if df.empty:
        return []

    # Select only string-like columns for keyword matching.
    text_df = df.select_dtypes(include=["object", "string"]).fillna("")
    if text_df.empty:
        return []

    pattern = re.escape(query.strip())
    mask = text_df.apply(lambda col: col.str.contains(pattern, case=False, na=False))
    row_mask = mask.any(axis=1)
    if not row_mask.any():
        return []

    matched = df[row_mask].copy()
    if "content" in matched.columns:
        matched["content"] = matched["content"].astype(str)
    matched = matched.head(limit)

    documents: List[Document] = []
    for _, row in matched.iterrows():
        page_content = str(row.get("content", "")).strip()
        if not page_content:
            continue
        metadata = {
            column: row[column]
            for column in row.index
            if column != "content" and pd.notna(row[column])
        }
        documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


def _deduplicate_documents(documents: Sequence[Document]) -> List[Document]:
    """Remove duplicate documents while preserving order."""

    seen = set()
    unique_docs: List[Document] = []
    for doc in documents:
        key = (doc.page_content, tuple(sorted(doc.metadata.items())))
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)
    return unique_docs


def hybrid_search(query: str, db_dir: str, k: int = 5) -> List[Document]:
    """Return top-k documents combining vector similarity and keyword matches."""

    vector_docs = search_vector_db(query, db_dir=db_dir, k=k) or []
    keyword_docs = _iter_keyword_matches(query, limit=k)

    merged = list(vector_docs) + list(keyword_docs)
    deduped = _deduplicate_documents(merged)

    if len(deduped) >= k:
        return deduped[:k]

    # If we still have room, re-append keyword docs to reach k when available.
    for doc in keyword_docs:
        if doc not in deduped:
            deduped.append(doc)
            if len(deduped) == k:
                break

    return deduped
