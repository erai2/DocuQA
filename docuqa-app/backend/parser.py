import os, re, sqlite3, docx, hashlib, argparse

DB_PATH = "suri_m.db"

def get_hash(text):
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()

def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()

def classify_text(text):
    if "사례" in text and re.search(r"[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]", text):
        return "case_studies"
    if any(x in text for x in ["뜻", "정의", "의미", "…란", "이라 한다", "이라 불린다"]):
        return "terminology"
    if any(x in text for x in ["구조", "格", "勢", "응기", "合", "沖", "刑", "破", "穿", "入墓", "祿"]):
        return "basic_theory"
    return None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS terminology (id TEXT PRIMARY KEY, term TEXT, definition TEXT, expanded TEXT, category TEXT, sources TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS basic_theory (id TEXT PRIMARY KEY, concept TEXT, definition TEXT, category TEXT, reference TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS case_studies (id TEXT PRIMARY KEY, chart TEXT, gender TEXT, analysis TEXT, conclusion TEXT, tags TEXT, expanded TEXT)")
    conn.commit()
    conn.close()

def insert_or_update(cur, table, uid, fields):
    if table == "terminology":
        cur.execute("INSERT OR REPLACE INTO terminology (id, term, definition, expanded, category, sources) VALUES (?, ?, ?, NULL, '용어', ?)", (uid, fields["term"], fields["text"], fields["source"]))
    elif table == "basic_theory":
        cur.execute("INSERT OR REPLACE INTO basic_theory (id, concept, definition, category, reference) VALUES (?, ?, ?, '이론', ?)", (uid, fields["term"], fields["text"], fields["source"]))
    elif table == "case_studies":
        cur.execute("INSERT OR REPLACE INTO case_studies (id, chart, gender, analysis, conclusion, tags, expanded) VALUES (?, 'unknown', NULL, ?, '', ?, NULL)", (uid, fields["text"], fields["source"]))

def parse_text(block, source, cur):
    block = normalize_text(block)
    category = classify_text(block)
    if not category: return
    uid = get_hash(block)
    fields = {"term": block.split()[0], "text": block, "source": source}
    insert_or_update(cur, category, uid, fields)

def process_docx(path, cur):
    doc = docx.Document(path)
    buffer = []
    for para in doc.paragraphs:
        txt = para.text.strip()
        if txt: buffer.append(txt)
        elif buffer:
            parse_text(" ".join(buffer).strip(), os.path.basename(path), cur)
            buffer = []
    if buffer:
        parse_text(" ".join(buffer).strip(), os.path.basename(path), cur)

def process_txt_md(path, cur):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    blocks = re.split(r"\n\s*\n", content)
    for block in blocks:
        if block.strip():
            parse_text(block.strip(), os.path.basename(path), cur)

def process_folder(folder_path):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith(".docx"):
                process_docx(filepath, cur)
            elif file.endswith(".txt") or file.endswith(".md"):
                process_txt_md(filepath, cur)
    conn.commit()
    conn.close()
    print("✅ 파싱 완료, DB 저장됨")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="수암명리 문서 파서")
    parser.add_argument("--folder", type=str, default="./documents", help="문서 폴더 경로")
    args = parser.parse_args()
    init_db()
    process_folder(args.folder)
