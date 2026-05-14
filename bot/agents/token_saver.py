"""
Token-Saver Agent — Groq (bepul, tez) bilan ishlaydi.
Vazifa murakkabligiga qarab model tanlaydi:

  llama-3.1-8b-instant    → Oddiy: tarjima, normalizatsiya (tez)
  llama-3.3-70b-versatile → O'rta va murakkab: tahlil, format

Groq bepul tier: 6,000 so'rov/kun — bu bot uchun yetarli.
"""

from __future__ import annotations
from groq import AsyncGroq
from loguru import logger
from bot.config import settings

FAST   = "llama-3.1-8b-instant"      # Oddiy vazifalar — juda tez
SMART  = "llama-3.3-70b-versatile"   # Murakkab vazifalar — aqlli

_COMPLEX_KEYWORDS = {
    "tahlil", "analyze", "explain", "reason", "chuqur", "murakkab",
    "compare", "evaluate", "strategiya", "architecture",
}
_MEDIUM_KEYWORDS = {
    "search", "find", "normalize", "translate", "format", "qidir",
    "tarjima", "tekshir", "check", "detect", "identify",
}

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


def select_model(task: str, estimated_tokens: int = 0) -> str:
    task_lower = task.lower()
    score = sum(3 for kw in _COMPLEX_KEYWORDS if kw in task_lower)
    score += sum(1 for kw in _MEDIUM_KEYWORDS if kw in task_lower)
    score += estimated_tokens // 300

    model = SMART if score >= 2 else FAST
    logger.debug(f"TokenSaver | task='{task[:40]}' score={score} → {model}")
    return model


async def call(
    system: str,
    user_message: str,
    task_description: str = "",
    max_tokens: int = 512,
    temperature: float = 0.3,
) -> str:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY .env faylida topilmadi")

    model  = select_model(task_description or user_message, max_tokens)
    client = _get_client()

    response = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": user_message},
        ],
    )

    result = response.choices[0].message.content
    usage  = response.usage
    logger.info(
        f"Groq | {model.split('-')[0]}-{model.split('-')[-1]} | "
        f"in={usage.prompt_tokens} out={usage.completion_tokens}"
    )
    return result
