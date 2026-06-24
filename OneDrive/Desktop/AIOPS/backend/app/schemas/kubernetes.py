from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class NamespaceResponse(BaseModel):
    name: str
    status: str
    created_at: datetime | None = None


class PodResponse(BaseModel):
    name: str
    namespace: str
    status: str
    ip: str | None = None
    node_name: str | None = None
    created_at: datetime | None = None


class ContainerStatus(BaseModel):
    name: str
    image: str
    ready: bool
    restart_count: int
    state: str


class PodDetailResponse(PodResponse):
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    containers: list[ContainerStatus] = Field(default_factory=list)


class PodEventResponse(BaseModel):
    type: str
    reason: str
    message: str
    source: str
    count: int | None = None
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None


class DeploymentResponse(BaseModel):
    name: str
    namespace: str
    replicas: int
    available_replicas: int
    ready_replicas: int
    updated_replicas: int
    created_at: datetime | None = None


class DeploymentCondition(BaseModel):
    type: str
    status: str
    reason: str | None = None
    message: str | None = None


class DeploymentStatusResponse(BaseModel):
    name: str
    namespace: str
    replicas: int
    available_replicas: int
    ready_replicas: int
    updated_replicas: int
    conditions: list[DeploymentCondition] = Field(default_factory=list)


class DeploymentScalePayload(BaseModel):
    replicas: int = Field(..., ge=0)


class DeploymentRollbackPayload(BaseModel):
    revision: int = Field(0, ge=0)


class NodeSummary(BaseModel):
    total: int
    ready: int
    not_ready: int


class PodSummary(BaseModel):
    total: int
    running: int
    pending: int
    failed: int
    unknown: int


class ClusterHealthResponse(BaseModel):
    status: str
    nodes: NodeSummary
    pods: PodSummary
    namespaces: list[str]
