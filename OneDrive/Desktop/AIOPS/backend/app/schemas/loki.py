from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    timestamp: datetime
    message: str
    pod: str | None = None
    namespace: str | None = None
    severity: str | None = None


class LogSearchResponse(BaseModel):
    query: str
    entries: list[LogEntry] = Field(default_factory=list)


class LiveLogEntry(BaseModel):
    timestamp: datetime
    message: str
    pod: str | None = None
    namespace: str | None = None


class LogAnalyticsResponse(BaseModel):
    error_count: int
    warning_count: int
    top_failing_pods: dict[str, int] = Field(default_factory=dict)
    top_failing_namespaces: dict[str, int] = Field(default_factory=dict)
