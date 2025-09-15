from modules.db import search_docs

def answer(query):
    results = search_docs(query)
    if not results:
        return "❌ 관련 자료를 찾을 수 없습니다."
    msg = "🔍 검색 결과:\n\n"
    for c, txt in results:
        msg += f"[{c}] {txt[:200]}...\n\n"
    return msg