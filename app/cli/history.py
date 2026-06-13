import json
import os
from pathlib import Path
from datetime import datetime


HISTORY_DIR = Path(os.getenv("NL2SQL_HISTORY_DIR", ".nl2sql"))
CHAT_HISTORY_FILE = HISTORY_DIR / "chat_history.json"
INPUT_HISTORY_FILE = HISTORY_DIR / "input_history.json"
DB_CONFIG_FILE = HISTORY_DIR / "db_config.json"


def _ensure_dir():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_input_history(history: list[str], max_size: int = 100) -> None:
    _ensure_dir()
    trimmed = history[-max_size:]
    INPUT_HISTORY_FILE.write_text(json.dumps(trimmed, ensure_ascii=False), encoding="utf-8")


def load_input_history(max_size: int = 100) -> list[str]:
    if not INPUT_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(INPUT_HISTORY_FILE.read_text(encoding="utf-8"))
        return data[-max_size:]
    except Exception:
        return []


def save_chat_message(role: str, content: str) -> None:
    _ensure_dir()
    messages = []
    if CHAT_HISTORY_FILE.exists():
        try:
            messages = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            messages = []

    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })

    if len(messages) > 500:
        messages = messages[-500:]

    CHAT_HISTORY_FILE.write_text(json.dumps(messages, ensure_ascii=False), encoding="utf-8")


def load_chat_history(max_size: int = 100) -> list[dict]:
    if not CHAT_HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
        return data[-max_size:]
    except Exception:
        return []


def clear_chat_history() -> None:
    if CHAT_HISTORY_FILE.exists():
        CHAT_HISTORY_FILE.unlink()


def save_db_config(database_url: str) -> None:
    _ensure_dir()
    DB_CONFIG_FILE.write_text(json.dumps({"database_url": database_url}, ensure_ascii=False), encoding="utf-8")


def load_db_config() -> str | None:
    if not DB_CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(DB_CONFIG_FILE.read_text(encoding="utf-8"))
        return data.get("database_url")
    except Exception:
        return None
