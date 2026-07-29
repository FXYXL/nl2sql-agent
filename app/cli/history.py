import json
import os
import re
from pathlib import Path
from datetime import datetime


HISTORY_DIR = Path(os.getenv("NL2SQL_HISTORY_DIR", ".nl2sql"))
CHAT_HISTORY_FILE = HISTORY_DIR / "chat_history.json"
INPUT_HISTORY_FILE = HISTORY_DIR / "input_history.json"
DB_CONFIG_FILE = HISTORY_DIR / "db_config.json"

_PASSWORD_PATTERN = re.compile(r'://([^:]+):([^@]+)@')

# 内存缓存，避免 save_chat_message 每次全量读写磁盘
_chat_cache: list[dict] | None = None


def _ensure_dir():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _mask_password(url: str) -> str:
    """脱敏 DATABASE_URL 中的密码"""
    return _PASSWORD_PATTERN.sub(r'://\1:***@', url)


def _unmask_password(url: str) -> str:
    """从环境变量恢复密码。保存的是脱敏 URL，加载时用环境变量 DATABASE_URL 中的密码替换"""
    env_url = os.getenv("DATABASE_URL", "")
    match_env = _PASSWORD_PATTERN.search(env_url)
    if match_env and '***' in url:
        user = match_env.group(1)
        pwd = match_env.group(2)
        return url.replace(f'{user}:***@', f'{user}:{pwd}@', 1)
    return url


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
    """追加聊天消息。使用内存缓存避免每次全量读写"""
    global _chat_cache
    _ensure_dir()

    if _chat_cache is None:
        _chat_cache = []
        if CHAT_HISTORY_FILE.exists():
            try:
                _chat_cache = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                _chat_cache = []

    _chat_cache.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })

    if len(_chat_cache) > 500:
        _chat_cache = _chat_cache[-500:]

    CHAT_HISTORY_FILE.write_text(json.dumps(_chat_cache, ensure_ascii=False), encoding="utf-8")


def load_chat_history(max_size: int = 100) -> list[dict]:
    global _chat_cache
    if _chat_cache is not None:
        return _chat_cache[-max_size:]

    if not CHAT_HISTORY_FILE.exists():
        _chat_cache = []
        return []
    try:
        data = json.loads(CHAT_HISTORY_FILE.read_text(encoding="utf-8"))
        _chat_cache = data
        return data[-max_size:]
    except Exception:
        _chat_cache = []
        return []


def clear_chat_history() -> None:
    global _chat_cache
    _chat_cache = []
    if CHAT_HISTORY_FILE.exists():
        CHAT_HISTORY_FILE.unlink()


def save_db_config(database_url: str) -> None:
    """保存数据库配置，密码脱敏后存储"""
    _ensure_dir()
    masked = _mask_password(database_url)
    DB_CONFIG_FILE.write_text(json.dumps({"database_url": masked}, ensure_ascii=False), encoding="utf-8")


def load_db_config() -> str | None:
    """加载数据库配置，尝试从环境变量恢复密码"""
    if not DB_CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(DB_CONFIG_FILE.read_text(encoding="utf-8"))
        url = data.get("database_url")
        if url:
            return _unmask_password(url)
        return None
    except Exception:
        return None
