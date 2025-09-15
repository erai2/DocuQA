import os
import sqlite3
import json

DB_PATH = "data/suri.db"
KEYWORD_PATH = "keywords.json"
EXPORT_DIR = "exports/keywords"

def load_keywords():
    with open(KEYWORD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def gather_context_for_keyword(keyword):
    """DB에서 해당 키워드가 포함된 content 모으기"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT title, content FROM concepts WHERE content LIKE ?", (f"%{keyword}%",))
    rows = cur.fetchall()
    conn.close()

    summary = ""
    for title, content in rows:
        snippet = content[:300].replace("\n", " ")
        summary += f"- **{title}**: {snippet}...\n"
    return summary if summary else "- (관련 내용 없음)\n"

def export_keyword_cards():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    keywords = load_keywords()

    for k in keywords:
        filename = os.path.join(EXPORT_DIR, f"{k['keyword']}.md")
        with open(filename, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write(f"키워드명: {k['keyword']}\n")
            f.write("================================================================================\n")
            f.write(f"분류: {k['category']}\n")
            f.write(f"설명: {k['desc']}\n\n")
            f.write("[관련 내용]\n")
            f.write("────────────────────────────────────────────────────────────────────────────────\n")
            f.write(gather_context_for_keyword(k["keyword"]))
            f.write("\n================================================================================\n")

    print(f"✅ {len(keywords)}개 키워드 카드가 '{EXPORT_DIR}/'에 저장되었습니다.")
