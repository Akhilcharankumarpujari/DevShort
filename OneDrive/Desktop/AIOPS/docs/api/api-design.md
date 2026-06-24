# API Design

## Overview

The backend exposes REST APIs through FastAPI. APIs are versioned under `/api/v1`. FastAPI will generate OpenAPI documentation once implementation begins.

## API Principles

- Version all public APIs.
- Use JSON request and response bodies.
- Use Pydantic v2 for validation.
- Return consistent error objects.
- Enforce RBAC at endpoint and object level.
- Use pagination for list endpoints.
- Use idempotency keys for ingestion and execution where appropriate.
- Never expose secrets in API responses.

## Base Path

```text
/api/v1
```

## Authentication

Protected endpoints use JWT bearer authentication.

```text
Authorization: Bearer <access_token>
```

## Standard Error Response

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "The requested resource was not found.",
    "details": {},
    "request_id": "req_123"
  }
}
```

## Pagination Pattern

```text
?page=1&page_size=25
```

Standard response:

```json
{
  "items": [],
  "page": 1,
  "page_size": 25,
  "total": 0
}
```

## Auth API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| POST | `/auth/login` | Authenticate user | Public |
| POST | `/auth/refresh` | Refresh access token | Public with refresh token |
| POST | `/auth/logout` | Logout current session | Authenticated |
| GET | `/auth/me` | Current user profile and permissions | Authenticated |

Login request:

```json
{
  "email": "sre@example.com",
  "password": "password"
}
```

Login response:

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Users API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/users` | List users | `users:read` |
| POST | `/users` | Create user | `users:create` |
| GET | `/users/{user_id}` | Get user | `users:read` |
| PATCH | `/users/{user_id}` | Update user | `users:update` |
| POST | `/users/{user_id}/disable` | Disable user | `users:disable` |
| POST | `/users/{user_id}/roles` | Assign role | `users:update` |
| DELETE | `/users/{user_id}/roles/{role_id}` | Remove role | `users:update` |

Query parameters for list:

- `page`
- `page_size`
- `status`
- `role`
- `search`

## Roles and Permissions API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/roles` | List roles | `roles:read` |
| POST | `/roles` | Create role | `roles:create` |
| GET | `/roles/{role_id}` | Get role | `roles:read` |
| PATCH | `/roles/{role_id}` | Update role | `roles:update` |
| GET | `/permissions` | List permissions | `permissions:read` |

## Incidents API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/incidents` | List incidents | `incidents:read` |
| POST | `/incidents` | Create manual incident | `incidents:create` |
| GET | `/incidents/{incident_id}` | Get incident | `incidents:read` |
| PATCH | `/incidents/{incident_id}` | Update incident | `incidents:update` |
| POST | `/incidents/{incident_id}/assign` | Assign owner | `incidents:assign` |
| POST | `/incidents/{incident_id}/acknowledge` | Acknowledge incident | `incidents:update` |
| POST | `/incidents/{incident_id}/mitigate` | Mark mitigated | `incidents:update` |
| POST | `/incidents/{incident_id}/resolve` | Resolve incident | `incidents:update` |
| POST | `/incidents/{incident_id}/close` | Close incident | `incidents:close` |
| GET | `/incidents/{incident_id}/timeline` | Incident timeline | `incidents:read` |
| POST | `/incidents/{incident_id}/comments` | Add comment | `incidents:comment` |
| GET | `/incidents/{incident_id}/rca` | RCA reports for incident | `rca:read` |

List query parameters:

- `status`
- `severity`
- `service_id`
- `cluster_id`
- `owner_id`
- `from`
- `to`
- `page`
- `page_size`

Create incident request:

```json
{
  "title": "Checkout API latency spike",
  "description": "p95 latency exceeded threshold",
  "severity": "sev2",
  "priority": "p2",
  "service_id": "uuid",
  "cluster_id": "uuid"
}
```

## Alerts API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/alerts` | List alerts | `alerts:read` |
| POST | `/alerts/ingest` | Ingest alert | Integration token or `alerts:ingest` |
| GET | `/alerts/{alert_id}` | Get alert | `alerts:read` |
| POST | `/alerts/{alert_id}/acknowledge` | Acknowledge alert | `alerts:update` |
| POST | `/alerts/{alert_id}/suppress` | Suppress alert | `alerts:update` |
| POST | `/alerts/{alert_id}/create-incident` | Create incident from alert | `incidents:create` |

List query parameters:

- `status`
- `severity`
- `source_id`
- `service_id`
- `cluster_id`
- `from`
- `to`
- `page`
- `page_size`

## Kubernetes API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/kubernetes/clusters` | List clusters | `kubernetes:read` |
| GET | `/kubernetes/clusters/{cluster_id}` | Get cluster | `kubernetes:read` |
| GET | `/kubernetes/clusters/{cluster_id}/namespaces` | List namespaces | `kubernetes:read` |
| GET | `/kubernetes/clusters/{cluster_id}/nodes` | List nodes | `kubernetes:read` |
| GET | `/kubernetes/clusters/{cluster_id}/workloads` | List workloads | `kubernetes:read` |
| GET | `/kubernetes/clusters/{cluster_id}/events` | List events | `kubernetes:read` |

Workload query parameters:

- `namespace`
- `kind`
- `status`
- `service_id`

## Metrics API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/metrics/query` | Query metrics | `metrics:read` |
| GET | `/metrics/incidents/{incident_id}` | Incident metric snapshots | `incidents:read` |

Metric query parameters:

- `source`
- `query`
- `start`
- `end`
- `step`

## Logs API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/logs/query` | Query logs | `logs:read` |
| GET | `/logs/incidents/{incident_id}` | Incident log findings | `incidents:read` |

Log query parameters:

- `source`
- `query`
- `start`
- `end`
- `limit`

## RCA API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| POST | `/rca/analyze` | Start RCA analysis | `rca:create` |
| GET | `/rca/reports/{report_id}` | Get RCA report | `rca:read` |

RCA request:

```json
{
  "incident_id": "uuid",
  "provider": "openai",
  "model": "model-name",
  "include_logs": true,
  "include_metrics": true,
  "include_kubernetes_events": true,
  "include_jenkins_context": true,
  "include_aws_context": true
}
```

RCA response:

```json
{
  "rca_report_id": "uuid",
  "status": "pending"
}
```

## Remediation API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/remediation/actions` | List action catalog | `remediation:read` |
| POST | `/remediation/recommend` | Recommend actions | `remediation:read` |
| POST | `/remediation/execute` | Request execution | `remediation:execute` |
| POST | `/remediation/executions/{execution_id}/approve` | Approve execution | `remediation:approve` |
| POST | `/remediation/executions/{execution_id}/cancel` | Cancel execution | `remediation:cancel` |
| GET | `/remediation/executions/{execution_id}` | Get execution status | `remediation:read` |

Execution request:

```json
{
  "incident_id": "uuid",
  "action_id": "uuid",
  "parameters": {},
  "approval_comment": "Restart deployment after confirmed memory leak"
}
```

## Integrations API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/integrations` | List integrations | `integrations:read` |
| POST | `/integrations` | Create integration | `integrations:create` |
| GET | `/integrations/{integration_id}` | Get integration | `integrations:read` |
| PATCH | `/integrations/{integration_id}` | Update integration | `integrations:update` |
| DELETE | `/integrations/{integration_id}` | Delete integration | `integrations:delete` |
| POST | `/integrations/{integration_id}/test` | Test integration | `integrations:test` |
| POST | `/integrations/{integration_id}/sync` | Sync integration | `integrations:sync` |

Integration types:

- prometheus
- loki
- grafana
- alertmanager
- kubernetes
- jenkins
- aws
- openai
- ollama

## Dashboard API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/dashboards/summary` | Operational summary | `dashboards:read` |
| GET | `/dashboards/incidents/trends` | Incident trends | `dashboards:read` |
| GET | `/dashboards/alerts/noise` | Alert noise analytics | `dashboards:read` |
| GET | `/dashboards/remediation/success-rate` | Remediation analytics | `dashboards:read` |

## Audit Logs API

| Method | Path | Purpose | Permission |
|---|---|---|---|
| GET | `/audit-logs` | Search audit logs | `audit_logs:read` |

Query parameters:

- `actor_id`
- `action`
- `resource_type`
- `resource_id`
- `outcome`
- `from`
- `to`
- `page`
- `page_size`

## Health API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Database and required dependency readiness |
| GET | `/health/integrations` | External integration health summary |

## RBAC Permission Matrix

| Capability | Admin | SRE | Developer | Viewer |
|---|---:|---:|---:|---:|
| View incidents | Yes | Yes | Yes | Yes |
| Create incidents | Yes | Yes | Yes | No |
| Update incidents | Yes | Yes | Limited | No |
| Close incidents | Yes | Yes | No | No |
| View alerts | Yes | Yes | Yes | Yes |
| Manage alert sources | Yes | Yes | No | No |
| Run RCA | Yes | Yes | Limited | No |
| View RCA | Yes | Yes | Yes | Yes |
| Execute remediation | Yes | Yes | Limited | No |
| Approve high-risk remediation | Yes | Yes | No | No |
| Manage integrations | Yes | Limited | No | No |
| Manage users and roles | Yes | No | No | No |
| View audit logs | Yes | Yes | No | No |
