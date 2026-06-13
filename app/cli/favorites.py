import json
import os
from pathlib import Path
from datetime import datetime


HISTORY_DIR = Path(os.getenv("NL2SQL_HISTORY_DIR", ".nl2sql"))
FAVORITES_FILE = HISTORY_DIR / "favorites.json"


def _ensure_dir():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_favorites() -> list[dict]:
    if not FAVORITES_FILE.exists():
        return []
    try:
        return json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_favorite(name: str, sql: str, question: str = "") -> None:
    _ensure_dir()
    favorites = load_favorites()
    favorites.append({
        "name": name,
        "sql": sql,
        "question": question,
        "created_at": datetime.now().isoformat(),
    })
    FAVORITES_FILE.write_text(json.dumps(favorites, ensure_ascii=False, indent=2), encoding="utf-8")


def remove_favorite(index: int) -> bool:
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        favorites.pop(index)
        FAVORITES_FILE.write_text(json.dumps(favorites, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    return False


def get_favorite(index: int) -> dict | None:
    favorites = load_favorites()
    if 0 <= index < len(favorites):
        return favorites[index]
    return None
