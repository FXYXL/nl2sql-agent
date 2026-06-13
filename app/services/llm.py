import logging

import httpx

from app.core.config import API_KEY, BASE_URL, LLM_MAX_RETRIES, LLM_TIMEOUT, MODEL_NAME

logger = logging.getLogger(__name__)


async def chat_completion(
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_retries: int | None = None,
) -> str:
    if max_retries is None:
        max_retries = LLM_MAX_RETRIES

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(LLM_TIMEOUT, connect=10.0),
            ) as client:
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
                content = data["choices"][0]["message"]["content"]
                if not content or not content.strip():
                    raise ValueError("LLM returned empty response")
                return content.strip()
        except httpx.TimeoutException:
            last_error = f"LLM request timed out (attempt {attempt}/{max_retries})"
            logger.warning(last_error)
        except httpx.HTTPStatusError as e:
            last_error = f"LLM HTTP {e.response.status_code} (attempt {attempt}/{max_retries})"
            logger.warning(last_error)
        except (KeyError, IndexError, ValueError) as e:
            last_error = f"LLM response parse error: {e} (attempt {attempt}/{max_retries})"
            logger.warning(last_error)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")
