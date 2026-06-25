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


class OllamaProvider(BaseAIProvider):
    """AI provider implementation targeting a local Ollama instance."""

    provider_name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3", timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
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
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                if resp.status_code != 200:
                    logger.error("Ollama API error: status=%s body=%s", resp.status_code, resp.text[:500])
                    raise AIProviderError(
                        f"Ollama API returned {resp.status_code}: {resp.text[:200]}",
                        provider="ollama",
                    )
                data = resp.json()
                content = data.get("message", {}).get("content", "{}")
                usage = data.get("eval_count", 0)
                rca: dict[str, Any] = cast(dict[str, Any], json.loads(content))
                rca["model_used"] = selected_model
                rca["tokens_used"] = {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": usage,
                    "total_tokens": data.get("prompt_eval_count", 0) + usage,
                }
                return rca
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.exception("Ollama connection failed")
            raise AIProviderError(f"Ollama connection failed: {exc}", provider="ollama", retryable=False) from exc
        except (json.JSONDecodeError, KeyError) as exc:
            logger.exception("Failed to parse Ollama response")
            result: dict[str, Any] = dict(_FALLBACK_RCA)
            result["model_used"] = selected_model
            result["tokens_used"] = {}
            return result
