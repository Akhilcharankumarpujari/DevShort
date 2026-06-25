from __future__ import annotations

import json
import logging
from typing import Any, cast

import httpx

from app.ai.providers.base import AIProviderError, BaseAIProvider

logger = logging.getLogger(__name__)

_FALLBACK_RCA: dict[str, Any] = {
    "root_cause": "Unable to parse AI response",
    "confidence_score": 0.0,
    "severity": "unknown",
    "impact": "Unknown — AI response was malformed",
    "recommendations": ["Review AI provider response manually"],
    "remediation_steps": [],
    "related_components": [],
}


class OpenAIProvider(BaseAIProvider):
    """AI provider implementation using OpenAI Chat Completions API."""

    provider_name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o", api_url: str = "https://api.openai.com/v1", timeout: int = 120) -> None:
        self.api_key = api_key
        self.model = model
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    async def generate_rca(
        self,
        user_prompt: str,
        system_prompt: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        selected_model = model or self.model
        payload = {
            "model": selected_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.api_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code != 200:
                    logger.error("OpenAI API error: status=%s body=%s", resp.status_code, resp.text[:500])
                    raise AIProviderError(
                        f"OpenAI API returned {resp.status_code}: {resp.text[:200]}",
                        provider="openai",
                    )
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                rca: dict[str, Any] = cast(dict[str, Any], json.loads(content))
                rca["model_used"] = selected_model
                rca["tokens_used"] = {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                }
                return rca
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.exception("OpenAI connection failed")
            raise AIProviderError(f"OpenAI connection failed: {exc}", provider="openai") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            logger.exception("Failed to parse OpenAI response")
            result: dict[str, Any] = dict(_FALLBACK_RCA)
            result["model_used"] = selected_model
            result["tokens_used"] = {}
            return result
