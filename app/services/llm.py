import httpx

from app.core.config import API_KEY, BASE_URL, MODEL_NAME


async def chat_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.0,
) -> str:
    """调用 OpenAI 兼容 API，返回模型回复文本。"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
