import os
import glob
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.parsing import parse_document
from core.database import insert_csv_to_db   # ✅ 교체

def build_databases(data_dir="data/raw_docs", db_dir="data/vector_db"):
    """
    data/raw_docs 안의 모든 문서를 파싱 → DB 저장 → VectorDB 빌드
    """
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    files = glob.glob(os.path.join(data_dir, "*"))
    if not files:
        print("[INFO] data/raw_docs 안에 문서가 없습니다.")
        return None

    all_cases, all_rules, all_concepts = [], [], []

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                text = f.read()
            cases, rules, concepts = parse_document(text)
            all_cases.extend(cases)
            all_rules.extend(rules)
            all_concepts.extend(concepts)
        except Exception as e:
            print(f"[ERROR] {file} 처리 중 오류: {e}")

    # --- SQLite 저장 ---
    if all_cases:
        insert_csv_to_db(pd.DataFrame(all_cases), table_name="cases")
    if all_rules:
        insert_csv_to_db(pd.DataFrame(all_rules), table_name="rules")
    if all_concepts:
        insert_csv_to_db(pd.DataFrame(all_concepts), table_name="concepts")

    # --- VectorDB 빌드 ---
    texts = []
    sources = []

    for c in all_cases:
        texts.append(c.get("detail", ""))
        sources.append("case")

    for r in all_rules:
        texts.append(r.get("desc", ""))
        sources.append("rule")

    for c in all_concepts:
        texts.append(c.get("desc", ""))
        sources.append("concept")

    if not texts:
        print("[INFO] 벡터화할 텍스트가 없습니다.")
        return None

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_texts(
        texts,
        embeddings,
        metadatas=[{"source": s} for s in sources],
        persist_directory=db_dir
    )
    vectorstore.persist()

    print(f"[INFO] ✅ DB 저장 완료 | 사례 {len(all_cases)}개, 규칙 {len(all_rules)}개, 개념 {len(all_concepts)}개")
    return vectorstore


def search_vector_db(query: str, db_dir="data/vector_db", k=3):
    """
    VectorDB에서 유사 검색
    """
    if not os.path.exists(db_dir):
        print("[WARN] VectorDB가 없습니다. 먼저 build_databases()를 실행하세요.")
        return []

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings)

    try:
        return vectorstore.similarity_search(query, k=k)
    except Exception as e:
        print(f"[ERROR] 검색 중 오류: {e}")
        return []
