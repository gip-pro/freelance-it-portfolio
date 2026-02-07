import json
import os
from typing import Set

def load_state(path: str) -> Set[str]:
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("processed_urls", []))

def save_state(path: str, processed_urls: Set[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"processed_urls": list(processed_urls)}, f)