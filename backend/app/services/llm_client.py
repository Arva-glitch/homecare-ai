"""Thin LLM client supporting Anthropic and OpenAI-compatible chat APIs via httpx.

Configured entirely through environment variables (LLM_PROVIDER, LLM_API_KEY,
LLM_MODEL, LLM_BASE_URL). Returns None on any failure so callers can fall back.
"""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)

DEFAULT_MODELS = {"anthropic": "claude-sonnet-4-5", "openai": "gpt-4o-mini"}


def chat_completion(system: str, messages: list[dict], max_tokens: int = 700) -> str | None:
    if not settings.llm_enabled:
        return None
    provider = (settings.LLM_PROVIDER or "anthropic").lower()
    model = settings.LLM_MODEL or DEFAULT_MODELS.get(provider, "gpt-4o-mini")
    try:
        if provider == "anthropic":
            url = (settings.LLM_BASE_URL or "https://api.anthropic.com") + "/v1/messages"
            r = httpx.post(url, timeout=settings.LLM_TIMEOUT_SECONDS, headers={
                "x-api-key": settings.LLM_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }, json={"model": model, "max_tokens": max_tokens, "system": system, "messages": messages})
            r.raise_for_status()
            data = r.json()
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip() or None
        # OpenAI-compatible
        url = (settings.LLM_BASE_URL or "https://api.openai.com/v1") + "/chat/completions"
        r = httpx.post(url, timeout=settings.LLM_TIMEOUT_SECONDS, headers={
            "Authorization": f"Bearer {settings.LLM_API_KEY}", "content-type": "application/json",
        }, json={"model": model, "max_tokens": max_tokens,
                 "messages": [{"role": "system", "content": system}] + messages})
        r.raise_for_status()
        return (r.json()["choices"][0]["message"]["content"] or "").strip() or None
    except Exception as exc:
        log.warning("LLM call failed (%s); using rule-based fallback", exc)
        return None
