from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    status: Literal["up", "down"]
    error: str | None = None


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: str
    version: str
    environment: str
    dependencies: dict[str, DependencyHealth]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
