from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProviderError(Exception):
    """Raised when an AI provider encounters an error."""

    def __init__(self, message: str, provider: str = "", retryable: bool = True) -> None:
        super().__init__(message)
        self.provider = provider
        self.retryable = retryable


class BaseAIProvider(ABC):
    """Abstract base class for all AI provider implementations."""

    provider_name: str = "base"

    @abstractmethod
    async def generate_rca(
        self,
        user_prompt: str,
        system_prompt: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        """
        Submit a prompt to the AI provider and return a structured RCA dict.

        Returns a dict with keys:
            root_cause, confidence_score, severity, impact,
            recommendations, remediation_steps, related_components,
            model_used, tokens_used
        """
        ...
