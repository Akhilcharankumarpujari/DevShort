from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
#  Sub-models                                                                   #
# --------------------------------------------------------------------------- #

class JenkinsHealthReport(BaseModel):
    score: int = 0
    description: str = ""


class JenkinsBuildSummary(BaseModel):
    number: int
    url: str
    result: str | None = None   # SUCCESS | FAILURE | ABORTED | UNSTABLE | None (building)
    duration_ms: int = 0
    timestamp: int = 0          # epoch millis from Jenkins
    building: bool = False
    description: str | None = None

    @property
    def started_at(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000)

    model_config = {"from_attributes": True}


class JenkinsBuildCause(BaseModel):
    short_description: str = ""


class JenkinsBuildArtifact(BaseModel):
    file_name: str
    relative_path: str


class JenkinsChangeSetEntry(BaseModel):
    commit_id: str | None = None
    author: str | None = None
    message: str | None = None
    timestamp: int | None = None


# --------------------------------------------------------------------------- #
#  Job schemas                                                                  #
# --------------------------------------------------------------------------- #

class JenkinsJobSummary(BaseModel):
    name: str
    url: str
    color: str = "notbuilt"  # blue, red, yellow, grey, notbuilt, disabled
    buildable: bool = True
    description: str | None = None

    model_config = {"from_attributes": True}


class JenkinsJobDetailResponse(BaseModel):
    name: str
    url: str
    color: str = "notbuilt"
    buildable: bool = True
    description: str | None = None
    health_reports: list[JenkinsHealthReport] = Field(default_factory=list)
    builds: list[JenkinsBuildSummary] = Field(default_factory=list)
    last_build: JenkinsBuildSummary | None = None
    last_successful_build: JenkinsBuildSummary | None = None
    last_failed_build: JenkinsBuildSummary | None = None

    model_config = {"from_attributes": True}


class JenkinsJobListResponse(BaseModel):
    total: int
    jobs: list[JenkinsJobSummary]


# --------------------------------------------------------------------------- #
#  Build schemas                                                                #
# --------------------------------------------------------------------------- #

class JenkinsBuildDetailResponse(BaseModel):
    number: int
    job_name: str
    url: str
    result: str | None = None
    duration_ms: int = 0
    estimated_duration_ms: int = 0
    timestamp: int = 0
    building: bool = False
    display_name: str | None = None
    description: str | None = None
    causes: list[JenkinsBuildCause] = Field(default_factory=list)
    artifacts: list[JenkinsBuildArtifact] = Field(default_factory=list)
    changeset: list[JenkinsChangeSetEntry] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class JenkinsBuildListResponse(BaseModel):
    total: int
    job_name: str
    builds: list[JenkinsBuildSummary]


# --------------------------------------------------------------------------- #
#  Action schemas                                                               #
# --------------------------------------------------------------------------- #

class JenkinsTriggerRequest(BaseModel):
    parameters: dict[str, str] = Field(default_factory=dict, description="Optional build parameters")


class JenkinsTriggerResponse(BaseModel):
    job_name: str
    queued: bool
    message: str


class JenkinsCancelResponse(BaseModel):
    job_name: str
    build_number: int
    cancelled: bool
    message: str


class JenkinsConsoleResponse(BaseModel):
    job_name: str
    build_number: int
    log: str
    size_bytes: int


# --------------------------------------------------------------------------- #
#  AI Analysis schemas                                                          #
# --------------------------------------------------------------------------- #

class JenkinsAnalyzeResponse(BaseModel):
    analysis_id: UUID
    job_name: str
    build_number: int
    build_result: str | None
    provider: str
    model: str
    root_cause: str
    confidence_score: float
    severity: str | None = None
    impact: str | None = None
    recommendations: list[Any] = Field(default_factory=list)
    remediation_steps: list[str] = Field(default_factory=list)
    related_components: list[str] = Field(default_factory=list)
