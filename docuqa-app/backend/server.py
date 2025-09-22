from fastapi import FastAPI
import sqlite3, os
import openai

app = FastAPI()
DB_PATH = "suri_m.db"

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/rules")
def get_rules():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT term, definition FROM terminology LIMIT 20")
        rows = cur.fetchall()
        return [{"term": r[0], "definition": r[1]} for r in rows]
    except:
        return []
    finally:
        conn.close()

@app.get("/analyze")
def analyze(question: str):
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "수암명리 DocuQA 분석기"},
            {"role": "user", "content": question}
        ]
    )
    return {"answer": response["choices"][0]["message"]["content"]}
