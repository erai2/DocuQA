import docx, os
from modules.db import insert_doc, init_db

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

    # 간단 분류
    if "허투" in text or "合" in text:
        category = "규칙"
    elif "격" in text:
        category = "개념"
    else:
        category = "사례"

    insert_doc(os.path.basename(filepath), category, text)