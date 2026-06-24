from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, UTC
from typing import Any, cast

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.metrics import MetricsSnapshot
from app.schemas.prometheus import (
    ClusterMetricsResponse,
    HistoricalSeries,
    HistoricalSeriesSample,
    HistoricalMetricsResponse,
    NamespaceMetricsResponse,
    NodeMetricsResponse,
    PodMetricsResponse,
)

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, default_ttl_seconds: int = 15) -> None:
        self._cache: dict[str, tuple[float, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        expires_at, value = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._cache[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        self._cache.clear()


# Global cache instance
_metrics_cache = MemoryCache()


class PrometheusService:
    def __init__(self, prometheus_url: str, session: AsyncSession) -> None:
        self.prometheus_url = prometheus_url.rstrip("/")
        self.session = session
        self.cache = _metrics_cache

    async def _query_instant(self, query: str) -> list[dict[str, Any]]:
        cached = self.cache.get(query)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        url = f"{self.prometheus_url}/api/v1/query"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params={"query": query}, timeout=10.0)
                if resp.status_code != 200:
                    logger.error(
                        "Prometheus query failed: status=%s, body=%s",
                        resp.status_code,
                        resp.text,
                    )
                    raise AppException(
                        status_code=502,
                        code="prometheus_api_error",
                        message=f"Prometheus API returned error status {resp.status_code}",
                    )

                data = resp.json()
                if data.get("status") != "success":
                    raise AppException(
                        status_code=502,
                        code="prometheus_api_error",
                        message=f"Prometheus query error: {data.get('error', 'unknown error')}",
                    )

                result = data.get("data", {}).get("result", [])
                self.cache.set(query, result)
                return cast(list[dict[str, Any]], result)
        except httpx.RequestError as e:
            logger.exception("Connection to Prometheus failed")
            raise AppException(
                status_code=503,
                code="prometheus_connection_error",
                message="Failed to connect to the Prometheus server.",
            ) from e

    async def _query_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: int,
    ) -> list[dict[str, Any]]:
        url = f"{self.prometheus_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "step": str(step),
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=15.0)
                if resp.status_code != 200:
                    logger.error(
                        "Prometheus query range failed: status=%s, body=%s",
                        resp.status_code,
                        resp.text,
                    )
                    raise AppException(
                        status_code=502,
                        code="prometheus_api_error",
                        message=f"Prometheus API returned error status {resp.status_code}",
                    )

                data = resp.json()
                if data.get("status") != "success":
                    raise AppException(
                        status_code=502,
                        code="prometheus_api_error",
                        message=f"Prometheus query error: {data.get('error', 'unknown error')}",
                    )

                return cast(list[dict[str, Any]], data.get("data", {}).get("result", []))
        except httpx.RequestError as e:
            logger.exception("Connection to Prometheus failed")
            raise AppException(
                status_code=503,
                code="prometheus_connection_error",
                message="Failed to connect to the Prometheus server.",
            ) from e

    async def get_nodes_metrics(self) -> list[NodeMetricsResponse]:
        # 1. Fetch Node CPU, Mem, Disk, Net Rx, Net Tx
        cpu_q = '100 * (1 - avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))'
        mem_q = "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
        disk_q = '100 * (1 - (node_filesystem_free_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"}))'
        rx_q = "sum by(instance) (rate(node_network_receive_bytes_total[5m]))"
        tx_q = "sum by(instance) (rate(node_network_transmit_bytes_total[5m]))"

        cpu_res, mem_res, disk_res, rx_res, tx_res = await asyncio.gather(
            self._query_instant(cpu_q),
            self._query_instant(mem_q),
            self._query_instant(disk_q),
            self._query_instant(rx_q),
            self._query_instant(tx_q),
        )

        nodes_data: dict[str, dict[str, float]] = {}

        def get_instance(metric: dict[str, str]) -> str:
            val = metric.get("instance", "unknown")
            return val.split(":")[0]  # strip port

        for r in cpu_res:
            inst = get_instance(r["metric"])
            nodes_data.setdefault(inst, {})["cpu"] = float(r["value"][1])
        for r in mem_res:
            inst = get_instance(r["metric"])
            nodes_data.setdefault(inst, {})["memory"] = float(r["value"][1])
        for r in disk_res:
            inst = get_instance(r["metric"])
            nodes_data.setdefault(inst, {})["disk"] = float(r["value"][1])
        for r in rx_res:
            inst = get_instance(r["metric"])
            nodes_data.setdefault(inst, {})["rx"] = float(r["value"][1])
        for r in tx_res:
            inst = get_instance(r["metric"])
            nodes_data.setdefault(inst, {})["tx"] = float(r["value"][1])

        return [
            NodeMetricsResponse(
                node_name=name,
                cpu_usage_pct=stats.get("cpu", 0.0),
                memory_usage_pct=stats.get("memory", 0.0),
                disk_usage_pct=stats.get("disk", 0.0),
                network_rx_bytes_sec=stats.get("rx", 0.0),
                network_tx_bytes_sec=stats.get("tx", 0.0),
            )
            for name, stats in nodes_data.items()
        ]

    async def get_pods_metrics(self, namespace: str | None = None) -> list[PodMetricsResponse]:
        ns_filter = f'namespace="{namespace}"' if namespace else ""
        container_filter = f'container!="",{ns_filter}'.strip(",")
        common_filter = f'{ns_filter}'.strip(",")

        cpu_q = f"sum by(pod, namespace) (rate(container_cpu_usage_seconds_total{{{container_filter}}}[5m]))"
        mem_q = f"sum by(pod, namespace) (container_memory_working_set_bytes{{{container_filter}}})"
        restarts_q = f"sum by(pod, namespace) (kube_pod_container_status_restarts_total{{{common_filter}}})"
        status_q = f"sum by(pod, namespace, status) (kube_pod_status_phase{{{common_filter}}})"

        cpu_res, mem_res, restarts_res, status_res = await asyncio.gather(
            self._query_instant(cpu_q),
            self._query_instant(mem_q),
            self._query_instant(restarts_q),
            self._query_instant(status_q),
        )

        pods_data: dict[tuple[str, str], dict[str, Any]] = {}

        for r in cpu_res:
            key = (r["metric"]["pod"], r["metric"]["namespace"])
            pods_data.setdefault(key, {})["cpu"] = float(r["value"][1])
        for r in mem_res:
            key = (r["metric"]["pod"], r["metric"]["namespace"])
            pods_data.setdefault(key, {})["memory"] = int(float(r["value"][1]))
        for r in restarts_res:
            key = (r["metric"]["pod"], r["metric"]["namespace"])
            pods_data.setdefault(key, {})["restarts"] = int(float(r["value"][1]))
        for r in status_res:
            key = (r["metric"]["pod"], r["metric"]["namespace"])
            pods_data.setdefault(key, {})["status"] = r["metric"].get("status", "Unknown")

        return [
            PodMetricsResponse(
                pod_name=k[0],
                namespace=k[1],
                cpu_cores=stats.get("cpu", 0.0),
                memory_bytes=stats.get("memory", 0),
                restarts=stats.get("restarts", 0),
                status=stats.get("status", "Running"),
            )
            for k, stats in pods_data.items()
        ]

    async def get_pod_metrics(self, name: str, namespace: str = "default") -> PodMetricsResponse:
        pods = await self.get_pods_metrics(namespace)
        for p in pods:
            if p.pod_name == name:
                return p
        raise AppException(
            status_code=404,
            code="prometheus_pod_not_found",
            message=f"Metrics for pod '{name}' in namespace '{namespace}' not found.",
        )

    async def get_namespace_metrics(self, namespace: str) -> NamespaceMetricsResponse:
        pods = await self.get_pods_metrics(namespace)
        cpu_sum = sum(p.cpu_cores for p in pods)
        mem_sum = sum(p.memory_bytes for p in pods)
        return NamespaceMetricsResponse(
            namespace=namespace,
            pod_count=len(pods),
            cpu_cores=cpu_sum,
            memory_bytes=mem_sum,
        )

    async def get_cluster_metrics(self) -> ClusterMetricsResponse:
        nodes_q = "count(kube_node_info)"
        nodes_ready_q = 'count(kube_node_status_condition{condition="Ready", status="true"})'
        pods_q = "count(kube_pod_info)"
        pods_running_q = 'sum(kube_pod_status_phase{phase="Running"})'
        pods_failed_q = 'sum(kube_pod_status_phase{phase="Failed"})'
        ns_pods_q = "sum by(namespace) (kube_pod_info)"

        n_res, nr_res, p_res, pr_res, pf_res, ns_res = await asyncio.gather(
            self._query_instant(nodes_q),
            self._query_instant(nodes_ready_q),
            self._query_instant(pods_q),
            self._query_instant(pods_running_q),
            self._query_instant(pods_failed_q),
            self._query_instant(ns_pods_q),
        )

        n_total = int(float(n_res[0]["value"][1])) if n_res else 0
        n_ready = int(float(nr_res[0]["value"][1])) if nr_res else 0
        p_total = int(float(p_res[0]["value"][1])) if p_res else 0
        p_running = int(float(pr_res[0]["value"][1])) if pr_res else 0
        p_failed = int(float(pf_res[0]["value"][1])) if pf_res else 0

        # Query namespace cpu and memory to populate the namespace lists
        namespaces_summary = []
        for ns_item in ns_res:
            ns_name = ns_item["metric"]["namespace"]
            ns_pods_count = int(float(ns_item["value"][1]))
            # Query cpu/memory details for namespace
            try:
                ns_metrics = await self.get_namespace_metrics(ns_name)
                namespaces_summary.append(ns_metrics)
            except Exception:
                namespaces_summary.append(
                    NamespaceMetricsResponse(
                        namespace=ns_name,
                        pod_count=ns_pods_count,
                        cpu_cores=0.0,
                        memory_bytes=0,
                    )
                )

        return ClusterMetricsResponse(
            nodes_total=n_total,
            nodes_ready=n_ready,
            pods_total=p_total,
            pods_running=p_running,
            pods_failed=p_failed,
            namespaces=namespaces_summary,
        )

    async def get_historical_metrics(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: int,
        save_snapshot: bool = False,
        incident_id: uuid.UUID | None = None,
        system_id: uuid.UUID | None = None,
        summary: str | None = None,
    ) -> HistoricalMetricsResponse:
        raw_result = await self._query_range(query, start, end, step)

        series_list = []
        all_values = []

        for r in raw_result:
            samples = []
            for v in r["values"]:
                ts = datetime.fromtimestamp(v[0], UTC)
                val = float(v[1])
                samples.append(HistoricalSeriesSample(timestamp=ts, value=val))
                all_values.append(val)
            series_list.append(
                HistoricalSeries(metric_labels=r["metric"], samples=samples)
            )

        snapshot_id = None
        if save_snapshot:
            # Compute stats
            min_val = min(all_values) if all_values else 0.0
            max_val = max(all_values) if all_values else 0.0
            avg_val = sum(all_values) / len(all_values) if all_values else 0.0

            db_samples = [
                {
                    "metric": r["metric"],
                    "values": [[int(v[0]), float(v[1])] for v in r["values"]],
                }
                for r in raw_result
            ]

            snapshot = MetricsSnapshot(
                id=uuid.uuid4(),
                incident_id=incident_id,
                system_id=system_id,
                source="prometheus",
                query=query,
                time_range_start=start,
                time_range_end=end,
                step_seconds=step,
                summary=summary,
                samples=db_samples,
                statistics={
                    "min": min_val,
                    "max": max_val,
                    "avg": avg_val,
                    "count": len(all_values),
                },
                captured_at=datetime.now(UTC),
            )
            self.session.add(snapshot)
            await self.session.commit()
            snapshot_id = snapshot.id

        return HistoricalMetricsResponse(
            query=query,
            start_time=start,
            end_time=end,
            step_seconds=step,
            series=series_list,
            snapshot_id=snapshot_id,
        )


import asyncio
