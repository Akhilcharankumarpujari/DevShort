"""Tests for Phase 11: Jenkins Agent."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.jenkins_agent import JenkinsAgent, JenkinsAgentError
from app.schemas.jenkins import (
    JenkinsBuildDetailResponse,
    JenkinsBuildListResponse,
    JenkinsBuildSummary,
    JenkinsCancelResponse,
    JenkinsConsoleResponse,
    JenkinsJobDetailResponse,
    JenkinsJobListResponse,
    JenkinsJobSummary,
    JenkinsTriggerRequest,
    JenkinsTriggerResponse,
)
from app.services.jenkins_service import (
    JenkinsService,
    _infer_failure_reason,
    _result_to_severity,
)


# ---------------------------------------------------------------------------#
# Fixtures / helpers                                                          #
# ---------------------------------------------------------------------------#

def _make_agent(base_url: str = "http://jenkins:8080") -> JenkinsAgent:
    return JenkinsAgent(
        base_url=base_url,
        username="admin",
        api_token="token123",
        timeout=5,
    )


def _make_service(agent: JenkinsAgent | None = None) -> JenkinsService:
    mock_session = AsyncMock()
    return JenkinsService(agent=agent or _make_agent(), session=mock_session)


SAMPLE_JOB_LIST: dict[str, Any] = {
    "jobs": [
        {"name": "my-app", "url": "http://jenkins:8080/job/my-app/", "color": "blue", "buildable": True},
        {"name": "infra-deploy", "url": "http://jenkins:8080/job/infra-deploy/", "color": "red", "buildable": True},
    ]
}

SAMPLE_JOB_DETAIL: dict[str, Any] = {
    "name": "my-app",
    "url": "http://jenkins:8080/job/my-app/",
    "color": "red",
    "buildable": True,
    "description": "Main app pipeline",
    "healthReport": [{"score": 60, "description": "Build stability: 2 out of 5 builds failed."}],
    "builds": [
        {"number": 42, "url": "http://j/job/my-app/42/", "result": "FAILURE", "duration": 120000, "timestamp": 1700000000000, "building": False},
        {"number": 41, "url": "http://j/job/my-app/41/", "result": "SUCCESS", "duration": 95000, "timestamp": 1699990000000, "building": False},
    ],
    "lastBuild": {"number": 42, "url": "http://j/job/my-app/42/", "result": "FAILURE", "duration": 120000, "timestamp": 1700000000000, "building": False},
    "lastSuccessfulBuild": {"number": 41, "url": "http://j/job/my-app/41/", "result": "SUCCESS", "duration": 95000, "timestamp": 1699990000000, "building": False},
    "lastFailedBuild": {"number": 42, "url": "http://j/job/my-app/42/", "result": "FAILURE", "duration": 120000, "timestamp": 1700000000000, "building": False},
}

SAMPLE_BUILD_DETAIL: dict[str, Any] = {
    "number": 42,
    "url": "http://jenkins:8080/job/my-app/42/",
    "result": "FAILURE",
    "duration": 120000,
    "estimatedDuration": 100000,
    "timestamp": 1700000000000,
    "building": False,
    "displayName": "#42",
    "description": None,
    "causes": [{"shortDescription": "Started by user admin"}],
    "artifacts": [{"fileName": "app.jar", "relativePath": "target/app.jar"}],
    "changeSet": {
        "items": [
            {"commitId": "abc123", "author": {"fullName": "Dev User"}, "msg": "Fix null pointer", "timestamp": 1699999000000}
        ]
    },
}


# ---------------------------------------------------------------------------#
# JenkinsAgent unit tests                                                     #
# ---------------------------------------------------------------------------#

class TestJenkinsAgent:
    def test_auth_header_is_base64_encoded(self) -> None:
        import base64
        agent = JenkinsAgent(base_url="http://j:8080", username="user", api_token="tok")
        expected = base64.b64encode(b"user:tok").decode()
        assert agent._auth_header == f"Basic {expected}"

    def test_trailing_slash_stripped(self) -> None:
        agent = JenkinsAgent(base_url="http://j:8080/", username="u", api_token="t")
        assert agent.base_url == "http://j:8080"

    @pytest.mark.asyncio
    async def test_list_jobs_success(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_JOB_LIST

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            result = await agent.list_jobs()

        assert len(result["jobs"]) == 2
        assert result["jobs"][0]["name"] == "my-app"

    @pytest.mark.asyncio
    async def test_get_job_404_raises_agent_error(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "http://jenkins:8080/job/missing/api/json"
        mock_resp.text = "Not Found"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            with pytest.raises(JenkinsAgentError) as exc_info:
                await agent.get_job("missing")

        assert exc_info.value.status_code == 404
        assert exc_info.value.retryable is False

    @pytest.mark.asyncio
    async def test_trigger_build_returns_status_code(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 201

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            code = await agent.trigger_build("my-app")

        assert code == 201

    @pytest.mark.asyncio
    async def test_stop_build_returns_status_code(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            code = await agent.stop_build("my-app", 42)

        assert code == 200

    @pytest.mark.asyncio
    async def test_get_console_output_returns_text(self) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Build started...\nERROR: Compilation failed\n"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            text = await agent.get_console_output("my-app", 42)

        assert "ERROR" in text

    @pytest.mark.asyncio
    async def test_connection_error_raises_agent_error(self) -> None:
        import httpx

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            agent = _make_agent()
            with pytest.raises(JenkinsAgentError) as exc_info:
                await agent.list_jobs()

        assert exc_info.value.status_code == 503


# ---------------------------------------------------------------------------#
# JenkinsService unit tests                                                   #
# ---------------------------------------------------------------------------#

class TestJenkinsService:
    @pytest.mark.asyncio
    async def test_list_jobs_maps_correctly(self) -> None:
        agent = _make_agent()
        agent.list_jobs = AsyncMock(return_value=SAMPLE_JOB_LIST)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.list_jobs()

        assert isinstance(result, JenkinsJobListResponse)
        assert result.total == 2
        assert result.jobs[0].name == "my-app"
        assert result.jobs[1].color == "red"

    @pytest.mark.asyncio
    async def test_get_job_maps_health_and_builds(self) -> None:
        agent = _make_agent()
        agent.get_job = AsyncMock(return_value=SAMPLE_JOB_DETAIL)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.get_job("my-app")

        assert isinstance(result, JenkinsJobDetailResponse)
        assert result.name == "my-app"
        assert len(result.builds) == 2
        assert result.last_build is not None
        assert result.last_build.result == "FAILURE"
        assert result.health_reports[0].score == 60

    @pytest.mark.asyncio
    async def test_get_build_history_returns_list(self) -> None:
        raw = {"builds": SAMPLE_JOB_DETAIL["builds"]}
        agent = _make_agent()
        agent.get_build_history = AsyncMock(return_value=raw)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.get_build_history("my-app", limit=10)

        assert isinstance(result, JenkinsBuildListResponse)
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_get_build_maps_changeset_and_causes(self) -> None:
        agent = _make_agent()
        agent.get_build = AsyncMock(return_value=SAMPLE_BUILD_DETAIL)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.get_build("my-app", 42)

        assert isinstance(result, JenkinsBuildDetailResponse)
        assert result.number == 42
        assert result.result == "FAILURE"
        assert result.causes[0].short_description == "Started by user admin"
        assert result.changeset[0].commit_id == "abc123"
        assert result.artifacts[0].file_name == "app.jar"

    @pytest.mark.asyncio
    async def test_trigger_build_queued_true(self) -> None:
        agent = _make_agent()
        agent.trigger_build = AsyncMock(return_value=201)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.trigger_build("my-app")

        assert isinstance(result, JenkinsTriggerResponse)
        assert result.queued is True
        assert "queued" in result.message.lower()

    @pytest.mark.asyncio
    async def test_cancel_build_cancelled_true(self) -> None:
        agent = _make_agent()
        agent.stop_build = AsyncMock(return_value=200)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.cancel_build("my-app", 42)

        assert isinstance(result, JenkinsCancelResponse)
        assert result.cancelled is True
        assert result.build_number == 42

    @pytest.mark.asyncio
    async def test_get_build_logs_returns_console(self) -> None:
        log_text = "Started by user admin\nBuild step 1\nERROR: Compilation failed\nBuild failed"
        agent = _make_agent()
        agent.get_console_output = AsyncMock(return_value=log_text)  # type: ignore[method-assign]
        svc = _make_service(agent)

        result = await svc.get_build_logs("my-app", 42)

        assert isinstance(result, JenkinsConsoleResponse)
        assert "ERROR" in result.log
        assert result.size_bytes == len(log_text.encode())

    @pytest.mark.asyncio
    async def test_agent_error_propagates_as_app_exception(self) -> None:
        from app.core.exceptions import AppException

        agent = _make_agent()
        agent.list_jobs = AsyncMock(side_effect=JenkinsAgentError("Not found", status_code=404))  # type: ignore[method-assign]
        svc = _make_service(agent)

        with pytest.raises(AppException) as exc_info:
            await svc.list_jobs()

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------#
# Helper function tests                                                        #
# ---------------------------------------------------------------------------#

class TestHelpers:
    def test_result_to_severity_failure(self) -> None:
        assert _result_to_severity("FAILURE") == "high"

    def test_result_to_severity_aborted(self) -> None:
        assert _result_to_severity("ABORTED") == "medium"

    def test_result_to_severity_success(self) -> None:
        assert _result_to_severity("SUCCESS") == "low"

    def test_result_to_severity_unknown(self) -> None:
        assert _result_to_severity("SOMETHING_ELSE") == "unknown"

    def test_infer_failure_reason_compilation(self) -> None:
        log = "... compilation error: cannot resolve symbol ..."
        assert _infer_failure_reason(log) == "Compilation error"

    def test_infer_failure_reason_test_failure(self) -> None:
        log = "Tests run: 5, Failures: 2, Errors: 0"
        assert _infer_failure_reason(log) == "Unit test failure"

    def test_infer_failure_reason_npm(self) -> None:
        log = "npm ERR! code ENOENT"
        assert _infer_failure_reason(log) == "npm error"

    def test_infer_failure_reason_unknown(self) -> None:
        log = "Some random output with no known failure keywords"
        assert _infer_failure_reason(log) == "Unknown build failure"

    def test_infer_failure_reason_docker(self) -> None:
        log = "docker: error response from daemon"
        assert _infer_failure_reason(log) == "Docker error"


# ---------------------------------------------------------------------------#
# Schema tests                                                                  #
# ---------------------------------------------------------------------------#

class TestSchemas:
    def test_job_summary_defaults(self) -> None:
        job = JenkinsJobSummary(name="test", url="http://j/job/test/")
        assert job.color == "notbuilt"
        assert job.buildable is True

    def test_build_summary_started_at(self) -> None:
        from datetime import datetime
        b = JenkinsBuildSummary(number=1, url="http://j/1/", timestamp=1700000000000)
        assert isinstance(b.started_at, datetime)

    def test_trigger_request_empty_params(self) -> None:
        req = JenkinsTriggerRequest()
        assert req.parameters == {}

    def test_trigger_request_with_params(self) -> None:
        req = JenkinsTriggerRequest(parameters={"BRANCH": "main", "ENV": "staging"})
        assert req.parameters["BRANCH"] == "main"


# ---------------------------------------------------------------------------#
# RBAC tests                                                                   #
# ---------------------------------------------------------------------------#

class TestJenkinsRBAC:
    def test_admin_has_all_jenkins_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.ADMIN.value]
        assert "jenkins:read" in perms
        assert "jenkins:write" in perms
        assert "jenkins:analyze" in perms

    def test_sre_has_all_jenkins_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.SRE.value]
        assert "jenkins:read" in perms
        assert "jenkins:write" in perms
        assert "jenkins:analyze" in perms

    def test_developer_has_all_jenkins_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.DEVELOPER.value]
        assert "jenkins:read" in perms
        assert "jenkins:write" in perms
        assert "jenkins:analyze" in perms

    def test_viewer_has_no_jenkins_permissions(self) -> None:
        from app.security.rbac import ROLE_PERMISSIONS, RoleName
        perms = ROLE_PERMISSIONS[RoleName.VIEWER.value]
        assert "jenkins:read" not in perms
        assert "jenkins:write" not in perms
        assert "jenkins:analyze" not in perms
