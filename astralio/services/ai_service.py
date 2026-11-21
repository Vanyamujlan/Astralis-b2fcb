"""Optional AI interpretation service with timeouts, rate limiting, and honest local fallback."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass

import httpx

from astralio.config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class InterpretationResult:
    """Result returned by AIService indicating whether AI or local fallback was used."""

    text: str
    source: str  # "ai" | "local_fallback"
    reason: str | None = None


class AIService:
    """Isolated optional LLM client for enriching astrology/tarot interpretations.

    - Reads API key strictly from Settings (environment variable AI_API_KEY).
    - Enforces request timeouts, error handling, and per-user rate limits.
    - Falls back transparently to local deterministic text whenever AI_API_KEY
      is not configured, rate-limited, or unavailable. Never disguises fallback
      text as an AI response.
    """

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = (
            settings.ai_api_key.get_secret_value().strip()
            if settings.ai_api_key is not None
            else ""
        )
        self._base_url = settings.ai_base_url.rstrip("/")
        self._model = settings.ai_model
        self._timeout = settings.ai_timeout_seconds
        self._rate_limit = settings.ai_rate_limit_per_minute
        self._http_client = http_client
        self._user_requests: dict[int, deque[float]] = defaultdict(deque)

    @property
    def is_enabled(self) -> bool:
        return bool(self._api_key)

    def _allow_request(self, user_id: int, now: float | None = None) -> bool:
        current = now if now is not None else time.monotonic()
        window = self._user_requests[user_id]
        cutoff = current - 60.0
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= self._rate_limit:
            return False
        window.append(current)
        return True

    async def enhance_interpretation(
        self,
        *,
        user_id: int,
        system_prompt: str,
        facts_prompt: str,
        local_fallback: str,
    ) -> InterpretationResult:
        """Optionally enrich factual astrological/tarot data via LLM with safe local fallback."""
        if not self.is_enabled:
            return InterpretationResult(
                text=local_fallback,
                source="local_fallback",
                reason="ai_not_configured",
            )

        if not self._allow_request(user_id):
            logger.info("AI rate limit reached for user=%s; using local fallback", user_id)
            return InterpretationResult(
                text=local_fallback,
                source="local_fallback",
                reason="rate_limited",
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "temperature": 0.5,
            "max_tokens": 450,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": facts_prompt},
            ],
        }

        try:
            if self._http_client is not None:
                response = await self._http_client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout,
                )
            else:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)

            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return InterpretationResult(
                    text=local_fallback,
                    source="local_fallback",
                    reason="empty_ai_response",
                )
            content = str(choices[0].get("message", {}).get("content", "")).strip()
            if not content:
                return InterpretationResult(
                    text=local_fallback,
                    source="local_fallback",
                    reason="empty_ai_content",
                )
            return InterpretationResult(text=content, source="ai")
        except httpx.TimeoutException:
            logger.warning("AI interpretation request timed out after %.1fs", self._timeout)
            return InterpretationResult(
                text=local_fallback,
                source="local_fallback",
                reason="timeout",
            )
        except Exception as exc:
            logger.warning(
                "AI interpretation request failed (%s); using local fallback", type(exc).__name__
            )
            return InterpretationResult(
                text=local_fallback,
                source="local_fallback",
                reason="upstream_error",
            )
