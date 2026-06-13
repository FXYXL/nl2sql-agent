import os
import sys

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")

MAX_SQL_ROWS = int(os.getenv("MAX_SQL_ROWS", "1000"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120.0"))


def validate_config():
    missing = []
    if not DATABASE_URL:
        missing.append("DATABASE_URL")
    if not API_KEY:
        missing.append("API_KEY")
    if not BASE_URL:
        missing.append("BASE_URL")
    if not MODEL_NAME:
        missing.append("MODEL_NAME")
    if missing:
        print(f"[FATAL] Missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
