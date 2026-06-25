"""Tests for Phase 10: AI Root Cause Analysis Engine."""
from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.prompt_manager import PromptManager, PromptTemplate
from app.ai.providers.base import AIProviderError, BaseAIProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.schemas.ai import (
    AnalysisResultResponse,
    AnalyzeIncidentRequest,
    AnalyzePodRequest,
    TokenUsage,
)


# ---------------------------------------------------------------------------#
#  Helpers                                                                    #
# ---------------------------------------------------------------------------#

SAMPLE_RCA: dict[str, Any] = {
    "root_cause": "Memory leak in user-service due to unclosed DB connections",
    "confidence_score": 0.87,
    "severity": "high",
    "impact": "User-facing latency spikes and eventual OOM kills",
    "recommendations": ["Increase memory limit to 512Mi", "Add connection pool max size"],
    "remediation_steps": ["kubectl rollout restart deployment/user-service -n production"],
    "related_components": ["user-service", "postgres"],
    "model_used": "llama3",
    "tokens_used": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
}


# ---------------------------------------------------------------------------#
#  PromptManager tests                                                        #
# ---------------------------------------------------------------------------#


class TestPromptManager:
    def test_detect_crashloop(self) -> None:
        t = PromptManager.detect_template("CrashLoopBackOff in user-service", {})
        assert t == PromptTemplate.CRASHLOOP_BACKOFF

    def test_detect_oom(self) -> None:
        t = PromptManager.detect_template("OOMKilled pod detected", {})
        assert t == PromptTemplate.OOM_KILLED

    def test_detect_high_cpu(self) -> None:
        t = PromptManager.detect_template("High CPU throttling on worker", {})
        assert t == PromptTemplate.HIGH_CPU

    def test_detect_kubernetes_via_label(self) -> None:
        t = PromptManager.detect_template("Deployment unavailable", {"alertname": "KubePodNotReady"})
        assert t == PromptTemplate.KUBERNETES_FAILURE

    def test_detect_generic_fallback(self) -> None:
        t = PromptManager.detect_template("Something went wrong", {})
        assert t == PromptTemplate.GENERIC_INCIDENT

    def test_build_prompt_fills_context(self) -> None:
        ctx = {
            "title": "Test Incident",
            "description": "A test",
            "severity": "high",
            "source": "prometheus",
            "labels": "{}",
            "namespace": "default",
            "pod": "test-pod",
            "logs": "log line 1",
            "events": "event 1",
            "alerts": "alert 1",
            "metrics": "cpu=80%",
        }
        prompt = PromptManager.build_prompt(PromptTemplate.GENERIC_INCIDENT, ctx)
        assert "Test Incident" in prompt
        assert "log line 1" in prompt

    def test_build_prompt_handles_missing_keys(self) -> None:
        """Missing keys should render as '<not available>'."""
        prompt = PromptManager.build_prompt(PromptTemplate.GENERIC_INCIDENT, {"title": "Partial"})
        assert "<not available>" in prompt

    def test_system_prompt_is_not_empty(self) -> None:
        sp = PromptManager.get_system_prompt()
        assert len(sp) > 100
        assert "JSON" in sp


# ---------------------------------------------------------------------------#
#  Provider tests                                                             #
# ---------------------------------------------------------------------------#


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_successful_generate(self) -> None:
        response_body = {
            "message": {"content": json.dumps(SAMPLE_RCA)},
            "eval_count": 200,
            "prompt_eval_count": 100,
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_body

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            provider = OllamaProvider(model="llama3")
            result = await provider.generate_rca("user prompt", "system prompt")

        assert result["root_cause"] == SAMPLE_RCA["root_cause"]
        assert result["model_used"] == "llama3"
        assert result["tokens_used"]["total_tokens"] == 300

    @pytest.mark.asyncio
    async def test_http_error_raises_ai_provider_error(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            provider = OllamaProvider()
            with pytest.raises(AIProviderError):
                await provider.generate_rca("user prompt", "system prompt")

    @pytest.mark.asyncio
    async def test_malformed_json_returns_fallback(self) -> None:
        response_body = {
            "message": {"content": "not valid json {{{"},
            "eval_count": 10,
            "prompt_eval_count": 5,
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_body

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            provider = OllamaProvider()
            result = await provider.generate_rca("user prompt", "system prompt")

        assert result["confidence_score"] == 0.0
        assert "Unable to parse" in result["root_cause"]


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_successful_generate(self) -> None:
        rca_json = json.dumps(SAMPLE_RCA)
        response_body = {
            "choices": [{"message": {"content": rca_json}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = response_body

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-test", model="gpt-4o")
            result = await provider.generate_rca("user prompt", "system prompt")

        assert result["root_cause"] == SAMPLE_RCA["root_cause"]
        assert result["model_used"] == "gpt-4o"
        assert result["tokens_used"]["prompt_tokens"] == 100

    @pytest.mark.asyncio
    async def test_auth_error_raises_ai_provider_error(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            provider = OpenAIProvider(api_key="bad-key")
            with pytest.raises(AIProviderError):
                await provider.generate_rca("user prompt", "system prompt")


# ---------------------------------------------------------------------------#
#  Schema tests                                                               #
# ---------------------------------------------------------------------------#


class TestSchemas:
    def test_analysis_result_response_coerces_decimal(self) -> None:
        from decimal import Decimal
        now = __import__("datetime").datetime.now()
        obj = AnalysisResultResponse(
            id=uuid.uuid4(),
            incident_id=None,
            analysis_type="rca",
            provider="ollama",
            model="llama3",
            status="completed",
            root_cause="test",
            confidence_score=Decimal("0.87"),  # type: ignore[arg-type]
            created_at=now,
        )
        assert abs(obj.confidence_score - 0.87) < 1e-9

    def test_analyze_incident_request_validates_uuid(self) -> None:
        req = AnalyzeIncidentRequest(incident_id=uuid.uuid4())
        assert isinstance(req.incident_id, uuid.UUID)

    def test_analyze_pod_request_defaults_namespace(self) -> None:
        req = AnalyzePodRequest(pod_name="my-pod")
        assert req.namespace == "default"

    def test_token_usage_defaults(self) -> None:
        t = TokenUsage()
        assert t.total_tokens == 0


# ---------------------------------------------------------------------------#
#  RBAC tests                                                                 #
# ---------------------------------------------------------------------------#


class TestRBACAIPermissions:
    def test_admin_has_ai_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.ADMIN.value]
        assert "ai:read" in perms
        assert "ai:analyze" in perms

    def test_sre_has_ai_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.SRE.value]
        assert "ai:read" in perms
        assert "ai:analyze" in perms

    def test_developer_has_ai_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.DEVELOPER.value]
        assert "ai:read" in perms
        assert "ai:analyze" in perms

    def test_viewer_does_not_have_ai_analyze(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.VIEWER.value]
        assert "ai:analyze" not in perms
