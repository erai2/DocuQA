import os
import json

SETTINGS_FILE = "data/settings.json"

DEFAULT_SETTINGS = {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 1000,
    "vector_weight": 0.6,
    "keyword_weight": 0.4
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()

def save_settings(new_settings: dict):
    settings = load_settings()
    settings.update(new_settings)
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def reset_settings():
    save_settings(DEFAULT_SETTINGS.copy())
