from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class JenkinsAgentError(Exception):
    """Raised when a Jenkins API call fails."""

    def __init__(self, message: str, status_code: int = 500, retryable: bool = True) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class JenkinsAgent:
    """
    Low-level async wrapper around the Jenkins REST API.

    All methods return raw dicts/strings and are transport-only — no
    business logic lives here. The JenkinsService layer is responsible
    for validation, schema mapping, and error translation.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        api_token: str,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # Basic auth header: username:api_token → base64
        raw = f"{username}:{api_token}".encode()
        self._auth_header = f"Basic {base64.b64encode(raw).decode()}"

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self._auth_header,
            "Accept": "application/json",
        }

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self._headers(), params=params or {})
                self._raise_for_status(resp)
                data: dict[str, Any] = resp.json()
                return data
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Jenkins GET %s failed: %s", path, exc)
            raise JenkinsAgentError(f"Connection to Jenkins failed: {exc}", status_code=503) from exc

    async def _get_text(self, path: str, params: dict[str, str] | None = None) -> str:
        url = f"{self.base_url}{path}"
        headers = {**self._headers(), "Accept": "text/plain"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers, params=params or {})
                self._raise_for_status(resp)
                return resp.text
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Jenkins GET-text %s failed: %s", path, exc)
            raise JenkinsAgentError(f"Connection to Jenkins failed: {exc}", status_code=503) from exc

    async def _post(self, path: str, data: dict[str, str] | None = None) -> int:
        """POST to Jenkins; returns HTTP status code."""
        url = f"{self.base_url}{path}"
        headers = {**self._headers(), "Content-Type": "application/x-www-form-urlencoded"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, data=data or {})
                return resp.status_code
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Jenkins POST %s failed: %s", path, exc)
            raise JenkinsAgentError(f"Connection to Jenkins failed: {exc}", status_code=503) from exc

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise JenkinsAgentError("Jenkins authentication failed — check JENKINS_USERNAME and JENKINS_API_TOKEN.", status_code=401, retryable=False)
        if resp.status_code == 403:
            raise JenkinsAgentError("Jenkins access forbidden.", status_code=403, retryable=False)
        if resp.status_code == 404:
            raise JenkinsAgentError(f"Jenkins resource not found: {resp.url}", status_code=404, retryable=False)
        if resp.status_code >= 400:
            raise JenkinsAgentError(f"Jenkins API error {resp.status_code}: {resp.text[:200]}", status_code=resp.status_code)

    # ------------------------------------------------------------------ #
    # Jobs                                                                 #
    # ------------------------------------------------------------------ #

    async def list_jobs(self) -> dict[str, Any]:
        """Return the top-level job list from the Jenkins API."""
        return await self._get("/api/json", params={"tree": "jobs[name,url,color,buildable,description]"})

    async def get_job(self, job_name: str) -> dict[str, Any]:
        """Return job detail including recent builds."""
        path = f"/job/{job_name}/api/json"
        return await self._get(
            path,
            params={
                "tree": (
                    "name,url,color,buildable,description,healthReport[score,description],"
                    "builds[number,url,result,duration,timestamp,building],"
                    "lastBuild[number,url,result,duration,timestamp,building],"
                    "lastSuccessfulBuild[number,url,result,timestamp],"
                    "lastFailedBuild[number,url,result,timestamp]"
                )
            },
        )

    async def get_build_history(self, job_name: str, limit: int = 25) -> dict[str, Any]:
        """Return a capped list of builds for a job."""
        builds_tree = f"builds[number,url,result,duration,timestamp,building,description]{{0,{limit}}}"
        return await self._get(
            f"/job/{job_name}/api/json",
            params={"tree": builds_tree},
        )

    # ------------------------------------------------------------------ #
    # Builds                                                               #
    # ------------------------------------------------------------------ #

    async def get_build(self, job_name: str, build_number: int) -> dict[str, Any]:
        """Return detail for a single build."""
        return await self._get(
            f"/job/{job_name}/{build_number}/api/json",
            params={
                "tree": (
                    "number,url,result,duration,timestamp,building,description,"
                    "displayName,fullDisplayName,estimatedDuration,"
                    "causes[shortDescription],"
                    "changeSet[items[commitId,author[fullName],msg,timestamp]],"
                    "artifacts[fileName,relativePath]"
                )
            },
        )

    async def trigger_build(self, job_name: str, parameters: dict[str, str] | None = None) -> int:
        """Trigger a new build. Returns the HTTP status (201 = queued)."""
        if parameters:
            return await self._post(f"/job/{job_name}/buildWithParameters", data=parameters)
        return await self._post(f"/job/{job_name}/build")

    async def stop_build(self, job_name: str, build_number: int) -> int:
        """Stop (cancel) a running build. Returns HTTP status."""
        return await self._post(f"/job/{job_name}/{build_number}/stop")

    async def get_console_output(self, job_name: str, build_number: int, start: int = 0) -> str:
        """Return raw console log text, optionally from a byte offset."""
        return await self._get_text(
            f"/job/{job_name}/{build_number}/logText/progressiveText",
            params={"start": str(start)},
        )
