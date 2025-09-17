import os
import json
from datetime import datetime

CHAT_DIR = "data/chats"
os.makedirs(CHAT_DIR, exist_ok=True)

_chat_history = []

def get_chat():
    return _chat_history

def add_message(role, content):
    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    _chat_history.append(msg)

def clear_chat():
    global _chat_history
    _chat_history = []

def export_chat(filename=None):
    if not filename:
        filename = datetime.now().strftime("chat_%Y%m%d_%H%M%S.json")
    path = os.path.join(CHAT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_chat_history, f, ensure_ascii=False, indent=2)
    return path

def import_chat(filename):
    path = os.path.join(CHAT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        clear_chat()
        for msg in data:
            _chat_history.append(msg)
        return True
    return False

def list_saved_chats():
    return [f for f in os.listdir(CHAT_DIR) if f.endswith(".json")]
