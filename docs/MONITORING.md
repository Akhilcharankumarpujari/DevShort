# DevShort — Monitoring Stack

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                         │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌───────────┐              │
│  │ Frontend │   │ Backend  │   │ PostgreSQL │              │
│  │  :5173   │   │  :4000   │   │   :5432    │              │
│  └──────────┘   └────┬─────┘   └───────────┘              │
│                      │ /metrics                             │
│                      ▼                                      │
│  ┌──────────┐   ┌───────────┐   ┌──────────┐              │
│  │ Grafana  │◄──│ Prometheus│──►│  Node    │              │
│  │  :3000   │   │   :9090   │   │ Exporter │              │
│  └──────────┘   └───────────┘   │  :9100   │              │
│                                 └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

**Data Flow:**

1. **Backend** exposes `GET /metrics` via `prom-client`, providing application-level metrics (HTTP requests, response times, memory, CPU, uptime).
2. **Node Exporter** exposes system-level metrics (CPU, memory, disk, network) at `:9100/metrics`.
3. **Prometheus** scrapes both targets every 15 seconds and stores time-series data in a persistent volume.
4. **Grafana** queries Prometheus and renders dashboards. All datasources and dashboards are auto-provisioned on first start — no manual configuration required.

---

## Services & Ports

| Service        | Container Name           | Port  | Description                          |
|----------------|--------------------------|-------|--------------------------------------|
| Prometheus     | `devshort-prometheus`    | 9090  | Time-series database & scraper       |
| Node Exporter  | `devshort-node-exporter` | 9100  | Host system metrics                  |
| Grafana        | `devshort-grafana`       | 3000  | Visualization & dashboards           |
| Backend        | `devshort-backend`       | 4000  | Application (`/metrics` endpoint)    |
| Frontend       | `devshort-frontend`      | 5173  | React SPA                            |
| PostgreSQL     | `devshort-postgres`      | 5432  | Database                             |

---

## How to Start

### Prerequisites

- Docker & Docker Compose installed
- Ports 3000, 4000, 5173, 5432, 9090, 9100 available

### Start the full stack

```bash
docker-compose up -d
```

This starts all services: PostgreSQL → Backend → Frontend + Prometheus + Node Exporter + Grafana.

### Start only the monitoring stack (if app is already running separately)

```bash
docker-compose up -d prometheus node-exporter grafana
```

### Environment Variables

| Variable              | Default | Description              |
|-----------------------|---------|--------------------------|
| `GRAFANA_ADMIN_USER`  | `admin` | Grafana admin username   |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |

Set these in `.env` or pass directly:

```bash
GRAFANA_ADMIN_PASSWORD=securepass docker-compose up -d grafana
```

---

## How to Verify

### 1. Check all containers are running

```bash
docker-compose ps
```

Expected: All 6 services show `Up` (healthy).

### 2. Verify Backend /metrics endpoint

```bash
curl http://localhost:4000/metrics
```

Expected output: Prometheus-formatted metrics including `devshort_http_requests_total`, `devshort_process_resident_memory_bytes`, etc.

### 3. Verify Prometheus targets

Open http://localhost:9090/targets

Expected: All 3 targets (`prometheus`, `devshort-backend`, `node-exporter`) show **State: UP**.

### 4. Verify Node Exporter

```bash
curl http://localhost:9100/metrics | head -20
```

Expected: System metrics like `node_cpu_seconds_total`, `node_memory_MemTotal_bytes`.

### 5. Verify Grafana

Open http://localhost:3000

- Login with `admin` / `admin` (or your custom credentials)
- Navigate to **Dashboards → DevShort** folder
- All 5 dashboards should be pre-loaded and displaying data

### 6. Test a PromQL query

Open http://localhost:9090 and run in the query box:

```promql
rate(devshort_http_requests_total[1m])
```

Expected: Returns the current request rate.

---

## Dashboard URLs

| Dashboard            | URL                                                    | UID                  |
|----------------------|--------------------------------------------------------|----------------------|
| Backend Overview     | http://localhost:3000/d/devshort-backend               | `devshort-backend`   |
| System Overview      | http://localhost:3000/d/devshort-system                | `devshort-system`    |
| HTTP Requests        | http://localhost:3000/d/devshort-requests              | `devshort-requests`  |
| Memory               | http://localhost:3000/d/devshort-memory                | `devshort-memory`    |
| CPU                  | http://localhost:3000/d/devshort-cpu                   | `devshort-cpu`       |

### What Each Dashboard Shows

**Backend Overview** — Application health status, process uptime, Node.js activity (handles/requests), request rate, response duration quantiles (p50/p95/p99), median & P99 latency gauges, memory usage over time, event loop lag, requests by status code, current throughput, 5xx error rate.

**System Overview** — Node Exporter status, CPU/Memory/Disk usage gauges, system uptime, CPU usage timeseries, memory usage (used/available/cache) timeseries, network throughput (RX/TX per device), disk usage by mount point, system load average (1m/5m/15m).

**HTTP Requests** — Request rate gauge, median/P95 response time gauges, 5xx error rate gauge, request rate by route, requests by status code (stacked bars), response time by route (p50/p95/p99 lines), average response size by route, error rate over time (4xx + 5xx).

**Memory** — RSS/Heap Used/Heap Total/External memory gauges, all process memory metrics over time, Node.js heap used vs total, GC duration rate, system memory usage %, system memory breakdown (total/free/available/buffers+cache).

**CPU** — System CPU usage gauge, backend process CPU gauge, system load gauge, event loop lag gauge, CPU usage breakdown (total/system/user/iowait), system load average, backend process CPU (user+system), event loop lag over time, Node.js active handles & requests.

---

## Metrics Reference

### Application Metrics (from `prom-client`)

| Metric                                         | Type      | Description                          |
|------------------------------------------------|-----------|--------------------------------------|
| `devshort_http_requests_total`                 | Counter   | Total HTTP requests (method, route, status_code) |
| `devshort_http_request_duration_seconds`       | Histogram | Request duration in seconds          |
| `devshort_http_response_size_bytes`            | Summary   | Response size in bytes               |
| `devshort_process_resident_memory_bytes`       | Gauge     | Process RSS memory                   |
| `devshort_process_heap_bytes`                  | Gauge     | Process heap size                    |
| `devshort_process_cpu_user_seconds_total`      | Counter   | Process user CPU time                |
| `devshort_process_cpu_system_seconds_total`    | Counter   | Process system CPU time              |
| `devshort_process_start_time_seconds`          | Gauge     | Process start time (for uptime calc) |
| `devshort_nodejs_eventloop_lag_seconds`        | Gauge     | Event loop lag                       |
| `devshort_nodejs_heap_size_used_bytes`         | Gauge     | Heap memory used                     |
| `devshort_nodejs_heap_size_total_bytes`        | Gauge     | Heap memory total                    |
| `devshort_nodejs_active_handles`               | Gauge     | Active libuv handles                 |
| `devshort_nodejs_active_requests`              | Gauge     | Active libuv requests                |

### System Metrics (from Node Exporter)

| Metric                          | Type    | Description               |
|---------------------------------|---------|---------------------------|
| `node_cpu_seconds_total`        | Counter | CPU time by mode          |
| `node_memory_MemTotal_bytes`    | Gauge   | Total system memory       |
| `node_memory_MemAvailable_bytes`| Gauge   | Available memory          |
| `node_memory_MemFree_bytes`     | Gauge   | Free memory               |
| `node_filesystem_avail_bytes`   | Gauge   | Available disk space      |
| `node_filesystem_size_bytes`    | Gauge   | Total disk space          |
| `node_network_receive_bytes_total`  | Counter | Network bytes received |
| `node_network_transmit_bytes_total` | Counter | Network bytes transmitted |
| `node_load1`/`node_load5`/`node_load15` | Gauge | System load average |
| `node_uptime_seconds`           | Gauge   | System uptime             |

---

## Configuration Files

| File                                                  | Purpose                                  |
|-------------------------------------------------------|------------------------------------------|
| `monitoring/prometheus/prometheus.yml`                | Prometheus scrape targets & rules        |
| `monitoring/grafana/provisioning/datasources/datasource.yml` | Auto-configures Prometheus datasource |
| `monitoring/grafana/provisioning/dashboards/dashboard.yml`  | Auto-loads dashboard JSON files      |
| `monitoring/grafana/dashboards/backend-overview.json` | Backend dashboard                        |
| `monitoring/grafana/dashboards/system-overview.json`  | System dashboard                         |
| `monitoring/grafana/dashboards/http-requests.json`    | HTTP requests dashboard                  |
| `monitoring/grafana/dashboards/memory.json`           | Memory dashboard                         |
| `monitoring/grafana/dashboards/cpu.json`              | CPU dashboard                            |
| `backend/src/middleware/metrics.js`                   | prom-client setup & metrics middleware   |

---

## Data Retention

- **Prometheus**: 15 days of time-series data (configurable via `--storage.tsdb.retention.time`)
- **Grafana**: Dashboards and settings persist in the `grafana_data` Docker volume
- **Prometheus data**: Persists in the `prometheus_data` Docker volume

---

## Stopping

```bash
# Stop all services (preserves volumes)
docker-compose down

# Stop all services and remove volumes (resets all monitoring data)
docker-compose down -v
```

---

## Troubleshooting

### Prometheus shows "Target down" for backend

Check the backend is running and healthy:

```bash
docker-compose ps backend
curl http://localhost:4000/api/health
curl http://localhost:4000/metrics
```

### Grafana dashboards show "No data"

1. Verify Prometheus is scraping: http://localhost:9090/targets
2. Verify the Prometheus datasource in Grafana: **Connections → Data Sources → Prometheus → Test**
3. Wait 1-2 minutes for enough data points to accumulate

### Port conflicts

If ports are in use, override in `.env` or `docker-compose.override.yml`:

```yaml
services:
  grafana:
    ports:
      - "4000:3000"  # Map to different host port
```
