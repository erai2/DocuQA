import os
import shutil
from langchain.schema import Document
from PyPDF2 import PdfReader

UPLOAD_DIR = "data/uploaded"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def list_files():
    return os.listdir(UPLOAD_DIR)

def remove_file(filename):
    path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(path):
        os.remove(path)

def clear_all_files():
    shutil.rmtree(UPLOAD_DIR)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def file_to_document(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    text = ""
    if ext in [".txt", ".md"]:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    elif ext == ".pdf":
        reader = PdfReader(filepath)
        text = "\n".join([page.extract_text() for page in reader.pages])
    else:
        return None
    return Document(page_content=text, metadata={"source": os.path.basename(filepath)})

def load_all_documents():
    docs = []
    for fname in list_files():
        path = os.path.join(UPLOAD_DIR, fname)
        doc = file_to_document(path)
        if doc:
            docs.append(doc)
    return docs
