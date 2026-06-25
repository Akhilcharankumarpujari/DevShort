from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompt_manager import PromptManager, PromptTemplate
from app.ai.providers.base import AIProviderError, BaseAIProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.models.alert import Alert
from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.models.incident import Incident

logger = logging.getLogger(__name__)


def _build_provider_chain(settings: Settings) -> list[BaseAIProvider]:
    """Build ordered list of providers with fallback chain."""
    providers: list[BaseAIProvider] = []

    if settings.ai_provider == "openai":
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        if api_key:
            providers.append(
                OpenAIProvider(
                    api_key=api_key,
                    model=settings.openai_model,
                    api_url=settings.openai_api_url,
                    timeout=settings.ai_request_timeout,
                )
            )
        # Fallback to Ollama
        providers.append(
            OllamaProvider(
                base_url=settings.ollama_url,
                model=settings.ollama_model,
                timeout=settings.ai_request_timeout,
            )
        )
    else:
        # Default: Ollama first, OpenAI as fallback if key present
        providers.append(
            OllamaProvider(
                base_url=settings.ollama_url,
                model=settings.ollama_model,
                timeout=settings.ai_request_timeout,
            )
        )
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        if api_key:
            providers.append(
                OpenAIProvider(
                    api_key=api_key,
                    model=settings.openai_model,
                    api_url=settings.openai_api_url,
                    timeout=settings.ai_request_timeout,
                )
            )
    return providers


async def _run_with_fallback(
    providers: list[BaseAIProvider],
    user_prompt: str,
    system_prompt: str,
    max_retries: int = 2,
) -> tuple[dict[str, Any], str]:
    """
    Try each provider in order with retries.
    Returns (rca_dict, provider_name_used).
    """
    last_exc: Exception | None = None
    for provider in providers:
        for attempt in range(max_retries):
            try:
                result = await provider.generate_rca(user_prompt, system_prompt)
                return result, provider.provider_name
            except AIProviderError as exc:
                last_exc = exc
                if not exc.retryable:
                    break
                logger.warning(
                    "AI provider '%s' attempt %d/%d failed: %s",
                    provider.provider_name,
                    attempt + 1,
                    max_retries,
                    exc,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        logger.error("All retries exhausted for provider '%s', trying next.", provider.provider_name)

    # All providers failed — return safe fallback
    fallback: dict[str, Any] = {
        "root_cause": f"AI analysis failed: {last_exc}",
        "confidence_score": 0.0,
        "severity": "unknown",
        "impact": "Unable to determine impact — AI unavailable",
        "recommendations": ["Manually investigate the incident"],
        "remediation_steps": [],
        "related_components": [],
        "model_used": "none",
        "tokens_used": {},
    }
    return fallback, "none"


class RCAEngine:
    """Orchestrates RCA analysis: collects context, calls AI, stores results."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self._providers = _build_provider_chain(settings)

    async def _save_analysis(
        self,
        *,
        incident_id: uuid.UUID | None = None,
        analysis_type: AnalysisType,
        rca: dict[str, Any],
        provider_name: str,
        started_at: float,
        context: dict[str, Any],
        creator_id: uuid.UUID | None = None,
    ) -> Analysis:
        completed_at = time.monotonic()
        duration_s = completed_at - started_at

        confidence_raw = rca.get("confidence_score", 0.0)
        try:
            confidence = Decimal(str(float(confidence_raw))).max(Decimal("0")).min(Decimal("1"))
        except Exception:
            confidence = Decimal("0")

        analysis = Analysis(
            incident_id=incident_id,
            created_by_id=creator_id,
            analysis_type=analysis_type.value,
            provider=provider_name,
            model=str(rca.get("model_used", "")),
            status=AnalysisStatus.COMPLETED.value,
            summary=rca.get("impact", ""),
            root_cause=rca.get("root_cause", ""),
            confidence_score=confidence,
            evidence=context,
            recommendations=[
                {"action": r} if isinstance(r, str) else r
                for r in rca.get("recommendations", [])
            ],
            prompt_version="v1",
            token_usage=rca.get("tokens_used", {}),
            started_at=datetime.fromtimestamp(time.time() - duration_s, UTC),
            completed_at=datetime.now(UTC),
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def analyze_incident(
        self,
        incident_id: uuid.UUID,
        creator_id: uuid.UUID | None = None,
    ) -> Analysis:
        stmt = select(Incident).where(Incident.id == incident_id, Incident.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        incident = res.scalars().first()
        if not incident:
            from app.core.exceptions import AppException
            raise AppException(status_code=404, code="incident_not_found", message=f"Incident '{incident_id}' not found.")

        labels: dict[str, str] = incident.labels or {}
        namespace = labels.get("namespace", "")
        pod = labels.get("pod", "")

        # Collect context (best-effort — errors are logged but don't fail the analysis)
        logs = await self._fetch_loki_logs(namespace=namespace, pod=pod)
        events = await self._fetch_k8s_events(namespace=namespace, pod=pod)
        alerts = await self._fetch_incident_alerts(incident_id)
        metrics = await self._fetch_pod_metrics(namespace=namespace, pod=pod)

        template = PromptManager.detect_template(incident.title, labels)
        context: dict[str, Any] = {
            "title": incident.title,
            "description": incident.description or "",
            "severity": incident.severity,
            "source": incident.source or "",
            "labels": json.dumps(labels),
            "namespace": namespace,
            "pod": pod,
            "logs": logs,
            "events": events,
            "alerts": alerts,
            "metrics": metrics,
            # template-specific extras (safe fallback to "<not available>")
            "exit_code": labels.get("exit_code", "<not available>"),
            "restart_count": labels.get("restart_count", "<not available>"),
            "last_state": labels.get("last_state", "<not available>"),
            "memory_limit": labels.get("memory_limit", "<not available>"),
            "memory_request": labels.get("memory_request", "<not available>"),
            "memory_metrics": metrics,
            "cpu_metrics": metrics,
            "node_status": "<not available>",
            "pod_status": "<not available>",
        }

        started_at = time.monotonic()
        user_prompt = PromptManager.build_prompt(template, context)
        system_prompt = PromptManager.get_system_prompt()
        rca, used_provider = await _run_with_fallback(
            self._providers, user_prompt, system_prompt, self.settings.ai_max_retries
        )
        return await self._save_analysis(
            incident_id=incident_id,
            analysis_type=AnalysisType.RCA,
            rca=rca,
            provider_name=used_provider,
            started_at=started_at,
            context=context,
            creator_id=creator_id,
        )

    async def analyze_alert(
        self,
        alert_id: uuid.UUID,
        creator_id: uuid.UUID | None = None,
    ) -> Analysis:
        stmt = select(Alert).where(Alert.id == alert_id, Alert.deleted_at.is_(None))
        res = await self.session.execute(stmt)
        alert = res.scalars().first()
        if not alert:
            from app.core.exceptions import AppException
            raise AppException(status_code=404, code="alert_not_found", message=f"Alert '{alert_id}' not found.")

        labels = alert.labels or {}
        namespace = labels.get("namespace", "")
        pod = labels.get("pod", "")

        logs = await self._fetch_loki_logs(namespace=namespace, pod=pod)
        events = await self._fetch_k8s_events(namespace=namespace, pod=pod)

        template = PromptManager.detect_template(alert.title, labels)
        context: dict[str, Any] = {
            "title": alert.title,
            "description": alert.description or "",
            "severity": alert.severity,
            "source": alert.source,
            "labels": json.dumps(labels),
            "namespace": namespace,
            "pod": pod,
            "logs": logs,
            "events": events,
            "alerts": json.dumps(alert.annotations),
            "metrics": "<not available>",
            "cpu_metrics": "<not available>",
            "memory_metrics": "<not available>",
            "node_status": "<not available>",
            "pod_status": "<not available>",
            "exit_code": labels.get("exit_code", "<not available>"),
            "restart_count": labels.get("restart_count", "<not available>"),
            "last_state": "<not available>",
            "memory_limit": "<not available>",
            "memory_request": "<not available>",
        }

        started_at = time.monotonic()
        user_prompt = PromptManager.build_prompt(template, context)
        system_prompt = PromptManager.get_system_prompt()
        rca, used_provider = await _run_with_fallback(
            self._providers, user_prompt, system_prompt, self.settings.ai_max_retries
        )
        incident_id = alert.incident_id
        return await self._save_analysis(
            incident_id=incident_id,
            analysis_type=AnalysisType.RCA,
            rca=rca,
            provider_name=used_provider,
            started_at=started_at,
            context=context,
            creator_id=creator_id,
        )

    async def analyze_pod(
        self,
        pod_name: str,
        namespace: str = "default",
        creator_id: uuid.UUID | None = None,
    ) -> Analysis:
        logs = await self._fetch_loki_logs(namespace=namespace, pod=pod_name)
        events = await self._fetch_k8s_events(namespace=namespace, pod=pod_name)
        metrics = await self._fetch_pod_metrics(namespace=namespace, pod=pod_name)

        template = PromptManager.detect_template(f"Pod issue: {pod_name}", {"pod": pod_name, "namespace": namespace})
        context: dict[str, Any] = {
            "title": f"Pod Analysis: {pod_name}",
            "description": f"AI analysis requested for pod '{pod_name}' in namespace '{namespace}'",
            "severity": "unknown",
            "source": "manual",
            "labels": json.dumps({"pod": pod_name, "namespace": namespace}),
            "namespace": namespace,
            "pod": pod_name,
            "logs": logs,
            "events": events,
            "alerts": "<not available>",
            "metrics": metrics,
            "cpu_metrics": metrics,
            "memory_metrics": metrics,
            "node_status": "<not available>",
            "pod_status": "<not available>",
            "exit_code": "<not available>",
            "restart_count": "<not available>",
            "last_state": "<not available>",
            "memory_limit": "<not available>",
            "memory_request": "<not available>",
        }

        started_at = time.monotonic()
        user_prompt = PromptManager.build_prompt(template, context)
        system_prompt = PromptManager.get_system_prompt()
        rca, used_provider = await _run_with_fallback(
            self._providers, user_prompt, system_prompt, self.settings.ai_max_retries
        )
        return await self._save_analysis(
            analysis_type=AnalysisType.RCA,
            rca=rca,
            provider_name=used_provider,
            started_at=started_at,
            context=context,
            creator_id=creator_id,
        )

    # ------------------------------------------------------------------ #
    # Context collection helpers — all best-effort, never throw to caller  #
    # ------------------------------------------------------------------ #

    async def _fetch_loki_logs(self, namespace: str, pod: str, limit: int = 50) -> str:
        try:
            from app.services.loki_service import LokiService
            svc = LokiService(self.settings.loki_url)
            entries = await svc.search_logs(
                namespace=namespace or None,
                pod=pod or None,
                limit=limit,
            )
            if not entries:
                return "<no logs available>"
            return "\n".join(
                f"[{(e.severity or 'info').upper()}] {e.timestamp.isoformat()} {e.message}"
                for e in entries
            )
        except Exception as exc:
            logger.warning("Failed to fetch Loki logs: %s", exc)
            return "<logs unavailable>"

    async def _fetch_k8s_events(self, namespace: str, pod: str) -> str:
        try:
            from app.agents.kubernetes_agent import KubernetesAgent
            from app.services.kubernetes_service import KubernetesService
            agent = KubernetesAgent()
            svc = KubernetesService(agent=agent, session=self.session)
            events = await svc.get_pod_events(name=pod or "unknown", namespace=namespace or "default")
            if not events:
                return "<no events available>"
            lines = []
            for ev in events[:20]:
                lines.append(f"[{ev.reason}] {ev.message}")
            return "\n".join(lines)
        except Exception as exc:
            logger.warning("Failed to fetch K8s events: %s", exc)
            return "<events unavailable>"

    async def _fetch_incident_alerts(self, incident_id: uuid.UUID) -> str:
        try:
            stmt = select(Alert).where(
                Alert.incident_id == incident_id,
                Alert.deleted_at.is_(None),
            )
            res = await self.session.execute(stmt)
            alerts = res.scalars().all()
            if not alerts:
                return "<no alerts>"
            return "\n".join(
                f"[{a.severity.upper()}] {a.title}: {a.description or ''}" for a in alerts
            )
        except Exception as exc:
            logger.warning("Failed to fetch incident alerts: %s", exc)
            return "<alerts unavailable>"

    async def _fetch_pod_metrics(self, namespace: str, pod: str) -> str:
        try:
            from app.services.prometheus_service import PrometheusService
            svc = PrometheusService(
                prometheus_url=self.settings.prometheus_url,
                session=self.session,
            )
            m = await svc.get_pod_metrics(name=pod, namespace=namespace or "default")
            return (
                f"CPU Cores: {m.cpu_cores:.4f}\n"
                f"Memory Bytes: {m.memory_bytes}\n"
                f"Restart Count: {m.restarts}\n"
                f"Status: {m.status}"
            )
        except Exception as exc:
            logger.warning("Failed to fetch Prometheus pod metrics: %s", exc)
            return "<metrics unavailable>"
