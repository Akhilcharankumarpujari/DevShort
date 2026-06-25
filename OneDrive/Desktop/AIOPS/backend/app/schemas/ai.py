from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
#  Request schemas                                                              #
# --------------------------------------------------------------------------- #

class AnalyzeIncidentRequest(BaseModel):
    incident_id: UUID = Field(..., description="ID of the incident to analyze")
    provider: str | None = Field(None, description="Override AI provider (openai | ollama)")


class AnalyzeAlertRequest(BaseModel):
    alert_id: UUID = Field(..., description="ID of the alert to analyze")
    provider: str | None = Field(None, description="Override AI provider (openai | ollama)")


class AnalyzePodRequest(BaseModel):
    pod_name: str = Field(..., min_length=1, description="Kubernetes pod name")
    namespace: str = Field("default", description="Kubernetes namespace")
    provider: str | None = Field(None, description="Override AI provider (openai | ollama)")


# --------------------------------------------------------------------------- #
#  Response schemas                                                             #
# --------------------------------------------------------------------------- #

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class AnalysisResultResponse(BaseModel):
    id: UUID
    incident_id: UUID | None
    analysis_type: str
    provider: str
    model: str
    status: str
    root_cause: str
    confidence_score: float
    severity: str | None = None
    impact: str | None = None
    recommendations: list[Any] = Field(default_factory=list)
    remediation_steps: list[str] = Field(default_factory=list)
    related_components: list[str] = Field(default_factory=list)
    token_usage: TokenUsage | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    @field_validator("confidence_score", mode="before")
    @classmethod
    def coerce_decimal(cls, v: Any) -> float:
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    model_config = {"from_attributes": True}


class AnalysisHistoryResponse(BaseModel):
    total: int
    items: list[AnalysisResultResponse]
