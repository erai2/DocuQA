import sqlite3, json

DB_PATH = "suri_m.db"

PREDEFINED_RULES = {
    "관인상생": {
        "definition": "官이 印을 生하여 日干을 돕는 구조",
        "conditions": ["관성 + 인성이 존재", "관 → 인 → 일간 흐름"],
        "results": ["관직, 승진, 명예"],
        "exceptions": ["허투, 입묘, 피상"]
    },
    "적포구조": {
        "definition": "강한 포신이 약한 적신을 완전 제압",
        "conditions": ["한쪽 세력 旺", "포신이 적신을 제압"],
        "results": ["안정적 성취"],
        "exceptions": ["포신 허투·입묘"]
    }
}

def expand_rules():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, term, definition, expanded, sources FROM terminology")
    rows = cur.fetchall()

    for uid, term, definition, expanded, sources in rows:
        if term in PREDEFINED_RULES:
            expanded_json = PREDEFINED_RULES[term]
        else:
            expanded_json = {"definition": definition or "", "conditions": [], "results": [], "exceptions": []}
        expanded_json["sources"] = sources or ""
        cur.execute("UPDATE terminology SET expanded=? WHERE id=?", (json.dumps(expanded_json, ensure_ascii=False), uid))

    conn.commit()
    conn.close()
    print("✅ 규칙 확장 완료")

if __name__ == "__main__":
    expand_rules()
