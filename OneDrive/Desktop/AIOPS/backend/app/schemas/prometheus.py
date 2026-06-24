from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class NodeMetricsResponse(BaseModel):
    node_name: str
    cpu_usage_pct: float
    memory_usage_pct: float
    disk_usage_pct: float
    network_rx_bytes_sec: float
    network_tx_bytes_sec: float


class PodMetricsResponse(BaseModel):
    pod_name: str
    namespace: str
    cpu_cores: float
    memory_bytes: int
    restarts: int
    status: str


class NamespaceMetricsResponse(BaseModel):
    namespace: str
    pod_count: int
    cpu_cores: float
    memory_bytes: int


class ClusterMetricsResponse(BaseModel):
    nodes_total: int
    nodes_ready: int
    pods_total: int
    pods_running: int
    pods_failed: int
    namespaces: list[NamespaceMetricsResponse] = Field(default_factory=list)


class HistoricalSeriesSample(BaseModel):
    timestamp: datetime
    value: float


class HistoricalSeries(BaseModel):
    metric_labels: dict[str, str] = Field(default_factory=dict)
    samples: list[HistoricalSeriesSample] = Field(default_factory=list)


class HistoricalMetricsResponse(BaseModel):
    query: str
    start_time: datetime
    end_time: datetime
    step_seconds: int
    series: list[HistoricalSeries] = Field(default_factory=list)
    snapshot_id: UUID | None = None  # Populated if save_snapshot=True


class MetricSnapshotResponse(BaseModel):
    id: UUID
    incident_id: UUID | None = None
    system_id: UUID | None = None
    source: str
    query: str
    time_range_start: datetime
    time_range_end: datetime
    step_seconds: int | None = None
    summary: str | None = None
    captured_at: datetime
    statistics: dict[str, object] = Field(default_factory=dict)

    class Config:
        from_attributes = True
