import json
import os

SETTINGS_FILE = "settings.json"

DEFAULTS = {
    "model": "gpt-4o-mini",
    "temperature": 0.3
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULTS
