import docx, os, sqlite3, re
from modules.db import insert_doc, init_db

def split_text(text: str):
    # ●, ※, 줄바꿈 2개 이상을 기준으로 쪼개기
    chunks = re.split(r"(?:●|※|\n{2,})", text)
    return [c.strip() for c in chunks if len(c.strip()) > 30]

def parse_docx_to_db(filepath):
    init_db()
    ext = os.path.splitext(filepath)[-1]
    text = ""

    if ext == ".docx":
        doc = docx.Document(filepath)
        for p in doc.paragraphs:
            text += p.text + "\n"
    else:  # txt 파일
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

    # 문단별 쪼개기
    chunks = split_text(text)

    # 간단 카테고리 분류
    for chunk in chunks:
        if "허투" in chunk or "合" in chunk:
            category = "규칙"
        elif "격" in chunk:
            category = "개념"
        else:
            category = "사례"

        insert_doc(os.path.basename(filepath), category, chunk)
