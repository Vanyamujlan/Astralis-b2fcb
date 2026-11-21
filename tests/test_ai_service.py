"""Tests for isolated AIService: fallback without key, timeout handling, rate limit, and mocked success."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from astralio.config import Settings
from astralio.services.ai_service import AIService


def _make_settings(*, ai_key: str = "", rate_limit: int = 5) -> Settings:
    return Settings(
        BOT_TOKEN="123456789:AAFakeTestTokenForPytestOnly1234567890",
        FIREBASE_PROJECT_ID="astralio-test",
        FIREBASE_CLIENT_EMAIL="test@astralio-test.iam.gserviceaccount.com",
        FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nTEST\\n-----END PRIVATE KEY-----\\n",
        AI_API_KEY=ai_key,
        AI_RATE_LIMIT_PER_MINUTE=rate_limit,
    )


@pytest.mark.asyncio
async def test_ai_service_falls_back_honestly_when_no_key() -> None:
    service = AIService(_make_settings(ai_key=""))
    assert service.is_enabled is False

    result = await service.enhance_interpretation(
        user_id=101,
        system_prompt="sys",
        facts_prompt="facts",
        local_fallback="Локальный разбор",
    )
    assert result.text == "Локальный разбор"
    assert result.source == "local_fallback"
    assert result.reason == "ai_not_configured"


@pytest.mark.asyncio
async def test_ai_service_returns_ai_text_on_success() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Глубокий AI-разбор по фактам карты."}}]
    }
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response

    service = AIService(_make_settings(ai_key="sk-test-fake-key-123456"), http_client=mock_client)
    assert service.is_enabled is True

    result = await service.enhance_interpretation(
        user_id=101,
        system_prompt="sys",
        facts_prompt="facts",
        local_fallback="Локальный разбор",
    )
    assert result.source == "ai"
    assert result.text == "Глубокий AI-разбор по фактам карты."


@pytest.mark.asyncio
async def test_ai_service_falls_back_on_timeout_and_error() -> None:
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.ReadTimeout("timeout")

    service = AIService(_make_settings(ai_key="sk-test-fake-key-123456"), http_client=mock_client)
    result = await service.enhance_interpretation(
        user_id=102,
        system_prompt="sys",
        facts_prompt="facts",
        local_fallback="Локальный разбор",
    )
    assert result.source == "local_fallback"
    assert result.reason == "timeout"
    assert result.text == "Локальный разбор"


@pytest.mark.asyncio
async def test_ai_service_enforces_per_user_rate_limit() -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"choices": [{"message": {"content": "OK AI"}}]}
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response

    service = AIService(
        _make_settings(ai_key="sk-test-fake-key-123456", rate_limit=2),
        http_client=mock_client,
    )

    r1 = await service.enhance_interpretation(
        user_id=500, system_prompt="s", facts_prompt="f", local_fallback="local"
    )
    r2 = await service.enhance_interpretation(
        user_id=500, system_prompt="s", facts_prompt="f", local_fallback="local"
    )
    r3 = await service.enhance_interpretation(
        user_id=500, system_prompt="s", facts_prompt="f", local_fallback="local"
    )

    assert r1.source == "ai"
    assert r2.source == "ai"
    assert r3.source == "local_fallback"
    assert r3.reason == "rate_limited"
