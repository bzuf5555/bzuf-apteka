"""
Token-Saver Agent
Vazifa murakkabligiga qarab Claude modelini avtomatik tanlaydi:
  - Haiku  → oddiy, tez, arzon (< 200 token)
  - Sonnet → o'rta murakkablik (200-800 token)
  - Opus   → chuqur tahlil (800+ token)
"""

from __future__ import annotations
import anthropic
from loguru import logger
from bot.config import settings

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"
OPUS = "claude-opus-4-7"

_COMPLEX_KEYWORDS = {
    "tahlil", "analyze", "explain", "reason", "chuqur", "murakkab",
    "compare", "evaluate", "strategiya", "architecture",
}
_MEDIUM_KEYWORDS = {
    "search", "find", "normalize", "translate", "format", "qidir",
    "tarjima", "tekshir", "check",
}

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def select_model(task: str, estimated_tokens: int = 0) -> str:
    """Vazifa matnini tahlil qilib, mos Claude modelini qaytaradi."""
    task_lower = task.lower()
    score = 0

    for kw in _COMPLEX_KEYWORDS:
        if kw in task_lower:
            score += 3
    for kw in _MEDIUM_KEYWORDS:
        if kw in task_lower:
            score += 1

    score += estimated_tokens // 300

    if score >= 5:
        model = OPUS
    elif score >= 2:
        model = SONNET
    else:
        model = HAIKU

    logger.debug(f"TokenSaver | task='{task[:50]}' score={score} → {model}")
    return model


async def call(
    system: str,
    user_message: str,
    task_description: str = "",
    max_tokens: int = 512,
    temperature: float = 0.3,
) -> str:
    """
    Claude API chaqiruvi — modelni avtomatik tanlaydi.

    Args:
        system: System prompt
        user_message: Foydalanuvchi xabari
        task_description: Murakkablikni baholash uchun tavsif (ixtiyoriy)
        max_tokens: Maksimal javob tokenlari
        temperature: Kreativlik darajasi (0=aniq, 1=ijodiy)

    Returns:
        Claude javobi (text)
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY .env faylida topilmadi")

    model = select_model(task_description or user_message, max_tokens)
    client = _get_client()

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        result = response.content[0].text
        logger.info(
            f"TokenSaver | model={model} "
            f"input={response.usage.input_tokens} "
            f"output={response.usage.output_tokens}"
        )
        return result
    except anthropic.APIError as e:
        logger.error(f"Claude API xatosi: {e}")
        raise
