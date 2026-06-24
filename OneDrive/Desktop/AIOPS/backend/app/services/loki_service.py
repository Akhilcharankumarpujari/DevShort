from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, UTC
from typing import Any, cast

import httpx

from app.core.exceptions import AppException
from app.schemas.loki import LiveLogEntry, LogAnalyticsResponse, LogEntry

logger = logging.getLogger(__name__)


class LokiService:
    def __init__(self, loki_url: str) -> None:
        self.loki_url = loki_url.rstrip("/")

    async def _query_range(
        self,
        query: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
        direction: str = "backward",
    ) -> list[dict[str, Any]]:
        url = f"{self.loki_url}/loki/api/v1/query_range"
        params: dict[str, str] = {
            "query": query,
            "limit": str(limit),
            "direction": direction,
        }
        if start:
            params["start"] = str(int(start.timestamp() * 1e9))
        if end:
            params["end"] = str(int(end.timestamp() * 1e9))

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=15.0)
                if resp.status_code != 200:
                    logger.error("Loki query range failed: status=%s, body=%s", resp.status_code, resp.text)
                    raise AppException(
                        status_code=502,
                        code="loki_api_error",
                        message=f"Loki API returned error status {resp.status_code}",
                    )
                data = resp.json()
                if data.get("status") != "success":
                    raise AppException(
                        status_code=502,
                        code="loki_api_error",
                        message=f"Loki query error: {data.get('error', 'unknown error')}",
                    )
                return cast(list[dict[str, Any]], data.get("data", {}).get("result", []))
        except httpx.RequestError as e:
            logger.exception("Connection to Loki failed")
            raise AppException(
                status_code=503,
                code="loki_connection_error",
                message="Failed to connect to the Loki server.",
            ) from e

    async def _query_instant(self, query: str) -> list[dict[str, Any]]:
        url = f"{self.loki_url}/loki/api/v1/query"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params={"query": query}, timeout=10.0)
                if resp.status_code != 200:
                    logger.error("Loki instant query failed: status=%s, body=%s", resp.status_code, resp.text)
                    raise AppException(
                        status_code=502,
                        code="loki_api_error",
                        message=f"Loki API returned error status {resp.status_code}",
                    )
                data = resp.json()
                if data.get("status") != "success":
                    raise AppException(
                        status_code=502,
                        code="loki_api_error",
                        message=f"Loki query error: {data.get('error', 'unknown error')}",
                    )
                return cast(list[dict[str, Any]], data.get("data", {}).get("result", []))
        except httpx.RequestError as e:
            logger.exception("Connection to Loki failed")
            raise AppException(
                status_code=503,
                code="loki_connection_error",
                message="Failed to connect to the Loki server.",
            ) from e

    def _build_logql(
        self,
        namespace: str | None = None,
        pod: str | None = None,
        deployment: str | None = None,
        severity: str | None = None,
        query: str | None = None,
    ) -> str:
        # Build stream selector
        selectors = []
        if namespace:
            selectors.append(f'namespace="{namespace}"')
        if pod:
            selectors.append(f'pod="{pod}"')
        if deployment:
            selectors.append(f'pod=~"^{deployment}-.*"')

        # Fallback to match everything if no selector specified
        logql = f"{{{','.join(selectors)}}}" if selectors else '{namespace=~".*"}'

        # Append filters
        if severity:
            logql += f' |~ "(?i){severity}"'
        if query:
            logql += f' |= "{query}"'

        return logql

    async def search_logs(
        self,
        *,
        query: str | None = None,
        namespace: str | None = None,
        pod: str | None = None,
        deployment: str | None = None,
        severity: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        logql = self._build_logql(namespace, pod, deployment, severity, query)
        raw_streams = await self._query_range(
            logql, start=start, end=end, limit=limit, direction="backward"
        )

        entries = []
        for stream in raw_streams:
            stream_labels = stream.get("stream", {})
            ns_label = stream_labels.get("namespace", "unknown")
            pod_label = stream_labels.get("pod", "unknown")

            for v in stream.get("values", []):
                ts_nano = int(v[0])
                msg = v[1]

                # Dynamically infer severity
                msg_lower = msg.lower()
                sev = "info"
                if any(x in msg_lower for x in ["error", "err", "fatal", "crit"]):
                    sev = "error"
                elif "warn" in msg_lower:
                    sev = "warning"
                elif "debug" in msg_lower:
                    sev = "debug"

                entries.append(
                    LogEntry(
                        timestamp=datetime.fromtimestamp(ts_nano / 1e9, UTC),
                        message=msg,
                        pod=pod_label,
                        namespace=ns_label,
                        severity=sev,
                    )
                )

        # Sort combined streams descending by timestamp
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]

    async def stream_live_logs(
        self,
        *,
        query: str | None = None,
        namespace: str | None = None,
        pod: str | None = None,
    ) -> AsyncIterator[str]:
        logql = self._build_logql(namespace=namespace, pod=pod, query=query)
        last_ts = datetime.now(UTC)

        while True:
            # Query range slightly in the future of last timestamp (+1ms)
            start_ns = int(last_ts.timestamp() * 1e9) + 1000000
            url = f"{self.loki_url}/loki/api/v1/query_range"
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(
                        url,
                        params={"query": logql, "start": str(start_ns), "limit": 50},
                        timeout=10.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_streams = data.get("data", {}).get("result", [])
                        new_events = []

                        for stream in raw_streams:
                            pod_label = stream.get("stream", {}).get("pod")
                            ns_label = stream.get("stream", {}).get("namespace")
                            for v in stream.get("values", []):
                                ts_nano = int(v[0])
                                msg = v[1]
                                new_events.append((ts_nano, msg, pod_label, ns_label))

                        # Sort oldest first so they stream in chronological order
                        new_events.sort(key=lambda x: x[0])
                        for ts_nano, msg, pod_l, ns_l in new_events:
                            last_ts = datetime.fromtimestamp(ts_nano / 1e9, UTC)
                            yield f"data: {LiveLogEntry(timestamp=last_ts, message=msg, pod=pod_l, namespace=ns_l).model_dump_json()}\n\n"
            except Exception:
                pass
            await asyncio.sleep(1.0)

    async def get_log_analytics(self, duration: str = "1h") -> LogAnalyticsResponse:
        error_q = f'sum(count_over_time({{namespace=~".*"}} |= "error" [{duration}]))'
        warn_q = f'sum(count_over_time({{namespace=~".*"}} |= "warn" [{duration}]))'
        top_pods_q = f'topk(5, sum by(pod) (count_over_time({{namespace=~".*"}} |= "error" [{duration}])))'
        top_ns_q = f'topk(5, sum by(namespace) (count_over_time({{namespace=~".*"}} |= "error" [{duration}])))'

        err_res, warn_res, pods_res, ns_res = await asyncio.gather(
            self._query_instant(error_q),
            self._query_instant(warn_q),
            self._query_instant(top_pods_q),
            self._query_instant(top_ns_q),
        )

        error_count = int(float(err_res[0]["value"][1])) if err_res else 0
        warn_count = int(float(warn_res[0]["value"][1])) if warn_res else 0

        top_failing_pods = {}
        for r in pods_res:
            pod_name = r["metric"].get("pod", "unknown")
            top_failing_pods[pod_name] = int(float(r["value"][1]))

        top_failing_namespaces = {}
        for r in ns_res:
            ns_name = r["metric"].get("namespace", "unknown")
            top_failing_namespaces[ns_name] = int(float(r["value"][1]))

        return LogAnalyticsResponse(
            error_count=error_count,
            warning_count=warn_count,
            top_failing_pods=top_failing_pods,
            top_failing_namespaces=top_failing_namespaces,
        )
