from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.jenkins_agent import JenkinsAgent, JenkinsAgentError
from app.core.config import Settings
from app.core.exceptions import AppException
from app.models.analysis import Analysis, AnalysisStatus, AnalysisType
from app.schemas.jenkins import (
    JenkinsBuildArtifact,
    JenkinsBuildCause,
    JenkinsBuildDetailResponse,
    JenkinsBuildListResponse,
    JenkinsBuildSummary,
    JenkinsCancelResponse,
    JenkinsChangeSetEntry,
    JenkinsConsoleResponse,
    JenkinsHealthReport,
    JenkinsJobDetailResponse,
    JenkinsJobListResponse,
    JenkinsJobSummary,
    JenkinsTriggerResponse,
)

logger = logging.getLogger(__name__)

# Maximum console log characters forwarded to AI to avoid token overflow
_MAX_LOG_CHARS = 8_000


def _agent_error_to_app_exception(exc: JenkinsAgentError) -> AppException:
    return AppException(
        status_code=exc.status_code,
        code="jenkins_error",
        message=str(exc),
    )


def _parse_build_summary(raw: dict[str, Any]) -> JenkinsBuildSummary:
    return JenkinsBuildSummary(
        number=int(raw.get("number", 0)),
        url=str(raw.get("url", "")),
        result=raw.get("result"),
        duration_ms=int(raw.get("duration", 0)),
        timestamp=int(raw.get("timestamp", 0)),
        building=bool(raw.get("building", False)),
        description=raw.get("description"),
    )


class JenkinsService:
    """Business-logic layer for Jenkins CI/CD operations."""

    def __init__(self, agent: JenkinsAgent, session: AsyncSession) -> None:
        self.agent = agent
        self.session = session

    # ------------------------------------------------------------------ #
    # Jobs                                                                 #
    # ------------------------------------------------------------------ #

    async def list_jobs(self) -> JenkinsJobListResponse:
        """Return all top-level Jenkins jobs."""
        try:
            data = await self.agent.list_jobs()
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        raw_jobs: list[dict[str, Any]] = data.get("jobs", [])
        jobs = [
            JenkinsJobSummary(
                name=str(j.get("name", "")),
                url=str(j.get("url", "")),
                color=str(j.get("color", "notbuilt")),
                buildable=bool(j.get("buildable", True)),
                description=j.get("description"),
            )
            for j in raw_jobs
        ]
        return JenkinsJobListResponse(total=len(jobs), jobs=jobs)

    async def get_job(self, job_name: str) -> JenkinsJobDetailResponse:
        """Return detailed information about a specific job."""
        try:
            data = await self.agent.get_job(job_name)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        health_reports = [
            JenkinsHealthReport(
                score=int(h.get("score", 0)),
                description=str(h.get("description", "")),
            )
            for h in (data.get("healthReport") or [])
        ]
        builds = [_parse_build_summary(b) for b in (data.get("builds") or [])]

        def _opt_build(raw: dict[str, Any] | None) -> JenkinsBuildSummary | None:
            return _parse_build_summary(raw) if raw else None

        return JenkinsJobDetailResponse(
            name=str(data.get("name", "")),
            url=str(data.get("url", "")),
            color=str(data.get("color", "notbuilt")),
            buildable=bool(data.get("buildable", True)),
            description=data.get("description"),
            health_reports=health_reports,
            builds=builds,
            last_build=_opt_build(data.get("lastBuild")),
            last_successful_build=_opt_build(data.get("lastSuccessfulBuild")),
            last_failed_build=_opt_build(data.get("lastFailedBuild")),
        )

    async def get_build_history(self, job_name: str, limit: int = 25) -> JenkinsBuildListResponse:
        """Return a paginated build history for a job."""
        try:
            data = await self.agent.get_build_history(job_name, limit=limit)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        builds = [_parse_build_summary(b) for b in (data.get("builds") or [])]
        return JenkinsBuildListResponse(total=len(builds), job_name=job_name, builds=builds)

    # ------------------------------------------------------------------ #
    # Builds                                                               #
    # ------------------------------------------------------------------ #

    async def get_build(self, job_name: str, build_number: int) -> JenkinsBuildDetailResponse:
        """Return full detail for a single build."""
        try:
            data = await self.agent.get_build(job_name, build_number)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        causes = [
            JenkinsBuildCause(short_description=str(c.get("shortDescription", "")))
            for c in (data.get("causes") or [])
        ]
        artifacts = [
            JenkinsBuildArtifact(
                file_name=str(a.get("fileName", "")),
                relative_path=str(a.get("relativePath", "")),
            )
            for a in (data.get("artifacts") or [])
        ]
        changeset_raw: list[dict[str, Any]] = (data.get("changeSet") or {}).get("items", [])
        changeset = [
            JenkinsChangeSetEntry(
                commit_id=c.get("commitId"),
                author=c.get("author", {}).get("fullName"),
                message=c.get("msg"),
                timestamp=c.get("timestamp"),
            )
            for c in changeset_raw
        ]

        return JenkinsBuildDetailResponse(
            number=int(data.get("number", build_number)),
            job_name=job_name,
            url=str(data.get("url", "")),
            result=data.get("result"),
            duration_ms=int(data.get("duration", 0)),
            estimated_duration_ms=int(data.get("estimatedDuration", 0)),
            timestamp=int(data.get("timestamp", 0)),
            building=bool(data.get("building", False)),
            display_name=data.get("displayName"),
            description=data.get("description"),
            causes=causes,
            artifacts=artifacts,
            changeset=changeset,
        )

    async def trigger_build(
        self,
        job_name: str,
        parameters: dict[str, str] | None = None,
    ) -> JenkinsTriggerResponse:
        """Queue a new build, optionally with parameters."""
        try:
            status_code = await self.agent.trigger_build(job_name, parameters)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        queued = status_code in (200, 201)
        return JenkinsTriggerResponse(
            job_name=job_name,
            queued=queued,
            message="Build queued successfully." if queued else f"Unexpected status: {status_code}",
        )

    async def cancel_build(self, job_name: str, build_number: int) -> JenkinsCancelResponse:
        """Stop a running build."""
        try:
            status_code = await self.agent.stop_build(job_name, build_number)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        cancelled = status_code in (200, 302)
        return JenkinsCancelResponse(
            job_name=job_name,
            build_number=build_number,
            cancelled=cancelled,
            message="Build cancelled." if cancelled else f"Unexpected status: {status_code}",
        )

    async def get_build_logs(self, job_name: str, build_number: int) -> JenkinsConsoleResponse:
        """Download the full console log for a build."""
        try:
            log_text = await self.agent.get_console_output(job_name, build_number)
        except JenkinsAgentError as exc:
            raise _agent_error_to_app_exception(exc) from exc

        return JenkinsConsoleResponse(
            job_name=job_name,
            build_number=build_number,
            log=log_text,
            size_bytes=len(log_text.encode()),
        )

    # ------------------------------------------------------------------ #
    # AI Analysis                                                          #
    # ------------------------------------------------------------------ #

    async def analyze_build(
        self,
        job_name: str,
        build_number: int,
        settings: Settings,
        creator_id: uuid.UUID | None = None,
    ) -> Analysis:
        """
        Collect build metadata and logs, then forward to the RCA Engine.
        The Analysis ORM object is stored and returned.
        """
        # 1. Fetch build detail (best-effort; errors raise AppException)
        build = await self.get_build(job_name, build_number)

        # 2. Fetch console log (best-effort — don't fail if oversized)
        log_text = "<console log unavailable>"
        try:
            console = await self.get_build_logs(job_name, build_number)
            log_text = console.log[-_MAX_LOG_CHARS:] if len(console.log) > _MAX_LOG_CHARS else console.log
        except AppException as exc:
            logger.warning("Could not fetch console log for analysis: %s", exc.message)

        # 3. Detect failure mode from result
        result = build.result or "UNKNOWN"
        is_failure = result in ("FAILURE", "ABORTED", "UNSTABLE")
        failure_reason = _infer_failure_reason(log_text) if is_failure else "Build did not fail"

        # 4. Build context dict for the RCA engine
        labels: dict[str, str] = {
            "job": job_name,
            "build_number": str(build_number),
            "result": result,
            "failure_reason": failure_reason,
        }
        context: dict[str, Any] = {
            "title": f"Jenkins Build Failure: {job_name} #{build_number}",
            "description": (
                f"Build #{build_number} of job '{job_name}' completed with result '{result}'. "
                f"Inferred failure reason: {failure_reason}"
            ),
            "severity": _result_to_severity(result),
            "source": "jenkins",
            "labels": str(labels),
            "namespace": "",
            "pod": "",
            "logs": log_text,
            "events": "<not available>",
            "alerts": "<not available>",
            "metrics": "<not available>",
            "cpu_metrics": "<not available>",
            "memory_metrics": "<not available>",
            "node_status": "<not available>",
            "pod_status": "<not available>",
            "exit_code": "<not available>",
            "restart_count": "<not available>",
            "last_state": "<not available>",
            "memory_limit": "<not available>",
            "memory_request": "<not available>",
            # Jenkins-specific template fields
            "job_name": job_name,
            "build_number": str(build_number),
            "failed_stage": failure_reason,
        }

        # 5. Use the Phase 10 RCA engine
        from app.ai.rca_engine import RCAEngine, _build_provider_chain, _run_with_fallback
        from app.ai.prompt_manager import PromptManager, PromptTemplate

        import time
        from datetime import UTC
        from datetime import datetime as _datetime

        providers = _build_provider_chain(settings)
        template = PromptTemplate.JENKINS_BUILD_FAILURE
        user_prompt = PromptManager.build_prompt(template, context)
        system_prompt = PromptManager.get_system_prompt()

        started_at = time.monotonic()
        rca, used_provider = await _run_with_fallback(providers, user_prompt, system_prompt, settings.ai_max_retries)

        # 6. Persist the analysis
        completed_at = time.monotonic()
        duration_s = completed_at - started_at

        confidence_raw = rca.get("confidence_score", 0.0)
        try:
            confidence = Decimal(str(float(confidence_raw))).max(Decimal("0")).min(Decimal("1"))
        except Exception:
            confidence = Decimal("0")

        analysis = Analysis(
            created_by_id=creator_id,
            analysis_type=AnalysisType.RCA.value,
            provider=used_provider,
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
            started_at=_datetime.fromtimestamp(time.time() - duration_s, UTC),
            completed_at=_datetime.now(UTC),
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def _result_to_severity(result: str) -> str:
    mapping = {
        "FAILURE": "high",
        "ABORTED": "medium",
        "UNSTABLE": "medium",
        "SUCCESS": "low",
    }
    return mapping.get(result, "unknown")


def _infer_failure_reason(log: str) -> str:
    """
    Heuristic scan of console log for common failure patterns.
    Returns a short phrase suitable for prompt injection.
    """
    log_lower = log.lower()

    patterns: list[tuple[str, str]] = [
        ("compilation error", "Compilation error"),
        ("build failed", "Build failed"),
        ("failed to download", "Dependency download failure"),
        ("cannot find symbol", "Missing symbol / compilation error"),
        ("no space left on device", "Disk full on build agent"),
        ("connection refused", "Network connection refused"),
        ("timeout", "Build timed out"),
        ("permission denied", "Permission denied"),
        ("test failure", "Unit test failure"),
        ("tests run:", "Unit test failure"),
        ("error:", "Generic build error"),
        ("exception in thread", "Unhandled Java exception"),
        ("npm err!", "npm error"),
        ("syntaxerror", "Syntax error"),
        ("modulenotfounderror", "Missing Python module"),
        ("docker: error", "Docker error"),
        ("image pull failure", "Docker image pull failure"),
    ]
    for keyword, label in patterns:
        if keyword in log_lower:
            return label
    return "Unknown build failure"
