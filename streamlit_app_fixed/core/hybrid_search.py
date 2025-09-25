from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def hybrid_search(query, db_dir="data/vector_db", top_k=5):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings)

    docs = vectorstore.similarity_search(query, k=top_k)

    texts = [d.page_content for d in docs]
    tfidf = TfidfVectorizer().fit(texts + [query])
    query_vec = tfidf.transform([query]).toarray()[0]
    doc_vecs = tfidf.transform(texts).toarray()

    scores = np.dot(doc_vecs, query_vec)
    hybrid_scores = [(doc, float(score)) for doc, score in zip(docs, scores)]
    hybrid_scores.sort(key=lambda x: x[1], reverse=True)

    return hybrid_scores[:top_k]
