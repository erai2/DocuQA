"""Utilities for parsing raw legal documents into structured datasets."""
from __future__ import annotations

import glob
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from modules.database import PRIMARY_KEYS, write_tables

RAW_DOCS_DIR = Path("data/raw_docs")
VECTOR_DB_DIR = Path("data/vector_db")
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

TAG_TO_TABLE = {
    "사례": "cases",
    "규칙": "rules",
    "개념": "concepts",
}


@dataclass
class BuildResult:
    """Return value for :func:`build_databases`."""

    success: bool
    message: str
    counts: Dict[str, int] = field(default_factory=dict)


def _iter_raw_files() -> Iterable[Path]:
    """Yield raw document files supported by the parser."""
    RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    patterns = ["*.txt", "*.md"]
    for pattern in patterns:
        for path in RAW_DOCS_DIR.glob(pattern):
            if path.is_file():
                yield path


def parse_text_to_chunks(text: str) -> List[Dict[str, str]]:
    """Split the provided raw text into tagged chunks."""
    chunks: List[Dict[str, str]] = []
    pattern = r"<(사례|규칙|개념)([^>]*)>(.*?)</\\1>"
    for match in re.finditer(pattern, text, re.DOTALL):
        tag = match.group(1)
        attrs = match.group(2)
        body = match.group(3)
        id_match = re.search(r'id="([^"]+)"', attrs)
        if not id_match:
            continue
        chunk_id = id_match.group(1).strip()
        content = re.sub(r"<[^>]+>", "", body).strip()
        title = content.splitlines()[0].strip() if content else chunk_id
        chunks.append(
            {
                "id": chunk_id,
                "type": tag,
                "title": title,
                "content": content,
            }
        )
    return chunks


def process_chunks_to_tables(chunks: List[Dict[str, str]]) -> Dict[str, pd.DataFrame]:
    """Organise chunk dictionaries into per-table data frames."""
    cases: List[Dict[str, str]] = []
    rules: List[Dict[str, str]] = []
    concepts: List[Dict[str, str]] = []
    links: List[Dict[str, str]] = []

    for chunk in chunks:
        table = TAG_TO_TABLE.get(chunk["type"])
        if table == "cases":
            cases.append(
                {
                    "case_id": chunk["id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                }
            )
            for link in _extract_rule_links(chunk["content"], chunk["id"]):
                links.append(link)
        elif table == "rules":
            rules.append(
                {
                    "rule_id": chunk["id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                }
            )
        elif table == "concepts":
            concepts.append(
                {
                    "concept_id": chunk["id"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                }
            )

    return {
        "cases": pd.DataFrame(cases, columns=["case_id", "title", "content"]),
        "rules": pd.DataFrame(rules, columns=["rule_id", "title", "content"]),
        "concepts": pd.DataFrame(concepts, columns=["concept_id", "title", "content"]),
        "case_rules_link": pd.DataFrame(links, columns=["case_id", "rule_id"]),
    }


def _extract_rule_links(content: str, case_id: str) -> List[Dict[str, str]]:
    """Helper to map rule ids referenced in a case to link rows."""
    match = re.search(r"\(규칙:\s*([^\)]+)\)", content)
    if not match:
        return []
    rule_ids = [item.strip() for item in match.group(1).split(",") if item.strip()]
    return [{"case_id": case_id, "rule_id": rule_id} for rule_id in rule_ids]


def _deduplicate_chunks(chunks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Remove duplicated chunk IDs while keeping the first occurrence."""
    seen = set()
    unique_chunks: List[Dict[str, str]] = []
    for chunk in chunks:
        if chunk["id"] in seen:
            continue
        seen.add(chunk["id"])
        unique_chunks.append(chunk)
    return unique_chunks


def _build_vector_store(documents: Iterable[Document]) -> None:
    """Persist the provided documents into a Chroma vector database."""
    docs = list(documents)
    if not docs:
        return

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    if VECTOR_DB_DIR.exists():
        shutil.rmtree(VECTOR_DB_DIR)
    Chroma.from_documents(docs, embeddings, persist_directory=str(VECTOR_DB_DIR))


def build_databases() -> BuildResult:
    """Parse raw documents, refresh the SQLite DB and rebuild the vector store."""
    try:
        files = list(_iter_raw_files())
        if not files:
            return BuildResult(False, "raw_docs 폴더에 처리할 문서가 없습니다.")

        chunks: List[Dict[str, str]] = []
        for path in files:
            with path.open("r", encoding="utf-8") as handle:
                chunks.extend(parse_text_to_chunks(handle.read()))

        if not chunks:
            return BuildResult(False, "문서에서 유효한 태그를 찾지 못했습니다.")

        unique_chunks = _deduplicate_chunks(chunks)
        tables = process_chunks_to_tables(unique_chunks)
        write_tables(tables)

        documents = []
        for table_name, df in tables.items():
            if table_name == "case_rules_link" or df.empty:
                continue
            for _, row in df.iterrows():
                metadata = {"source": table_name, "title": row.get("title", "")}
                pk = PRIMARY_KEYS.get(table_name)
                if pk and pk in row:
                    metadata["id"] = row[pk]
                lines = []
                for col in df.columns:
                    value = row.get(col)
                    if pd.notna(value):
                        lines.append(f"{col}: {value}")
                documents.append(
                    Document(page_content="\n".join(lines), metadata=metadata)
                )
        _build_vector_store(documents)

        counts = {name: int(len(df)) for name, df in tables.items() if df is not None}
        return BuildResult(True, "DB 및 벡터 DB 재구축을 완료했습니다.", counts)
    except Exception as exc:  # pragma: no cover - defensive logging
        return BuildResult(False, f"처리 중 오류가 발생했습니다: {exc}")


def list_raw_documents() -> List[Path]:
    """Return a sorted list of raw document paths available for processing."""
    return sorted(_iter_raw_files())

