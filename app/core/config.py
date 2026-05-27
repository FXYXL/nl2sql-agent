import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:aa123456@localhost:3306/geek_ai_assistant",
)

# LLM 配置（OpenAI 兼容格式）
API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "")
MODEL_NAME = os.getenv("MODEL_NAME", "")
