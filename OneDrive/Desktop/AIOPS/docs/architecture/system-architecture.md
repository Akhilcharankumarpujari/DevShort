# System Architecture

## Overview

The AIOps Platform is an AI-powered DevOps and SRE operations platform. It centralizes alerts, incidents, metrics, logs, Kubernetes events, Jenkins activity, and AWS infrastructure telemetry, then uses AI-assisted analysis to identify likely root causes and recommend controlled remediation actions.

The design follows Clean Architecture and Domain Driven Design. Core business logic stays independent from implementation details such as OpenAI, Ollama, Jenkins, AWS, Kubernetes, Prometheus, Loki, Grafana, Alertmanager, and PostgreSQL.

## Architecture Style

Primary layers:

- Presentation layer: React frontend and FastAPI route handlers.
- Application layer: use cases, commands, queries, orchestration, policies, and workflows.
- Domain layer: entities, value objects, domain services, business rules, and interfaces.
- Infrastructure layer: repositories, external API clients, cloud adapters, AI providers, queues, and persistence implementations.

Dependency direction:

```text
Presentation -> Application -> Domain
Infrastructure -> Application and Domain interfaces
Domain -> no external dependencies
```

## Bounded Contexts

### Identity and Access

Responsibilities:

- User authentication
- JWT token issuance and refresh
- Role and permission management
- RBAC policy enforcement
- Account lifecycle management

Built-in roles:

- Admin: full platform administration.
- SRE: incident response, RCA, remediation approval, and remediation execution.
- Developer: service-level visibility, incident collaboration, and limited remediation.
- Viewer: read-only operational visibility.

### Incident Management

Responsibilities:

- Incident creation and lifecycle management
- Severity, priority, ownership, assignment, and escalation
- Incident timeline and collaboration events
- Incident closure and post-incident linkage
- Relationships to alerts, logs, metrics, RCA reports, and remediation actions

### Alert Management

Responsibilities:

- Alert ingestion from Alertmanager, CloudWatch, Jenkins, and custom webhooks
- Alert normalization into a common model
- Deduplication and correlation
- Routing and severity mapping
- Alert-to-incident conversion

### Observability and Kubernetes Monitoring

Responsibilities:

- Kubernetes cluster inventory
- Namespace, node, workload, pod, service, and event visibility
- Prometheus metric queries
- Loki log queries
- Correlation of telemetry with incidents

### AI Root Cause Analysis

Responsibilities:

- Incident context gathering
- Metric and log summarization
- Kubernetes event correlation
- Jenkins deployment and build correlation
- AWS CloudWatch and resource correlation
- OpenAI and Ollama provider selection
- RCA report generation
- Confidence scoring and evidence tracking

### Auto Remediation

Responsibilities:

- Remediation recommendation catalog
- Manual approval workflow
- Execution guardrails
- Kubernetes remediation actions
- Jenkins job triggers
- AWS operational actions
- Execution tracking and rollback metadata

### Integrations

Responsibilities:

- Prometheus integration
- Alertmanager integration
- Loki integration
- Grafana integration
- Kubernetes integration
- Jenkins integration
- AWS integration
- OpenAI and Ollama integration

### Audit and Compliance

Responsibilities:

- Security event logging
- Incident workflow logging
- Remediation approval and execution logging
- Integration configuration change logging
- User and role change logging
- Immutable audit trail design

### Dashboard Analytics

Responsibilities:

- Incident trends
- MTTA and MTTR metrics
- Alert noise and deduplication analytics
- Service reliability views
- Remediation success rate
- AI RCA usage and quality analytics

## Main Components

### Frontend Web Application

The frontend is a React, Vite, and TypeScript application using Tailwind CSS, shadcn/ui, React Query, Axios, and React Router.

Primary modules:

- Authentication
- Dashboard
- Incidents
- Alerts
- Kubernetes
- Metrics
- Logs
- AI RCA
- Remediation
- Integrations
- Audit logs
- Administration

### Backend API

The backend is a FastAPI application exposing versioned REST APIs. It owns authentication, authorization, domain use cases, integration orchestration, and persistence.

Primary modules:

- API routers
- Application use cases
- Domain models and services
- SQLAlchemy repositories
- Integration clients
- AI providers
- Security services
- Background workers
- Observability middleware

### Background Workers

Background workers handle long-running and scheduled work.

Responsibilities:

- Alert processing
- Incident correlation
- RCA generation
- Telemetry collection
- Remediation execution
- Notification dispatch
- Integration health checks

### PostgreSQL

PostgreSQL stores transactional platform data, including users, roles, permissions, incidents, alerts, RCA reports, remediation executions, integrations, and audit logs.

### Prometheus and Alertmanager

Prometheus stores metrics. Alertmanager emits alerts into the platform through webhook ingestion.

### Loki and Promtail

Loki stores logs. Promtail collects and ships logs into Loki. The platform queries Loki for incident context and RCA evidence.

### Grafana

Grafana provides external dashboards and deep links from incidents to metric and log panels.

### AI Provider Layer

The AI provider layer supports OpenAI and Ollama behind a common interface.

Provider responsibilities:

- Chat completion
- Structured RCA output
- Prompt rendering
- Token and cost metadata
- Timeout and retry handling
- Provider health checks

### AWS Integration

AWS integration supports CloudWatch, EKS, EC2, RDS, S3, and IAM.

Responsibilities:

- Read CloudWatch alarms and metrics
- Discover EKS clusters and metadata
- Collect EC2 and RDS operational metadata
- Store exported artifacts in S3
- Use IAM roles and least-privilege access

## Key Workflows

### Alert to Incident

1. Alert arrives from Alertmanager, CloudWatch, Jenkins, or a custom webhook.
2. Backend validates and normalizes the payload.
3. Alert is deduplicated against active alerts.
4. Correlation rules evaluate service, cluster, namespace, severity, labels, and time window.
5. Existing incident is updated or a new incident is created.
6. Incident timeline is updated.
7. Audit log entry is recorded.
8. Dashboard and notification state are updated.

### AI RCA

1. User requests RCA or automatic RCA policy triggers analysis.
2. Platform gathers incident alerts, timeline, metrics, logs, Kubernetes events, Jenkins activity, and AWS context.
3. Context is summarized and redacted for sensitive values.
4. Selected AI provider receives a structured prompt.
5. RCA report is generated with summary, likely cause, evidence, confidence, and recommended remediation.
6. Report is stored and linked to the incident.
7. Audit log records the RCA request and provider metadata.

### Remediation

1. RCA or user selects a remediation action.
2. Platform validates role, permissions, policy, risk level, and target scope.
3. If required, approval is requested from an authorized user.
4. Execution engine runs the action through Kubernetes, Jenkins, AWS, or a manual runbook.
5. Execution result is stored.
6. Incident timeline and audit logs are updated.

## Security Architecture

Security controls:

- JWT access and refresh tokens
- Strong password hashing
- Role-based authorization
- Endpoint-level permission checks
- Object-level access checks
- Secrets stored outside source control
- Integration credentials encrypted or stored by external secret reference
- Audit logging for privileged actions
- Strict CORS configuration
- Request validation through Pydantic v2
- Rate limiting for authentication and ingestion endpoints
- Secret redaction before AI provider calls
- Least-privilege IAM policies for AWS
- Narrow Kubernetes service account RBAC

## Observability Architecture

Backend observability:

- Structured JSON logs
- Request correlation IDs
- OpenTelemetry-ready tracing
- Prometheus metrics endpoint
- Health, readiness, and liveness endpoints
- Integration health checks

Platform metrics:

- API latency and error rate
- Alert ingestion throughput
- RCA request count and duration
- AI provider latency and failure rate
- Remediation execution success and failure counts
- Incident MTTA and MTTR

## Deployment Architecture

Target production deployment:

- React frontend served through a containerized web service or static hosting.
- FastAPI backend deployed to Kubernetes.
- Background workers deployed separately from the API.
- PostgreSQL provided by AWS RDS or managed PostgreSQL.
- Prometheus, Grafana, Alertmanager, Loki, and Promtail deployed through Helm.
- Object storage provided by S3.
- Secrets managed through Kubernetes Secrets, AWS Secrets Manager, or External Secrets Operator.

## Scalability Model

Horizontal scaling:

- Backend API scales independently.
- Background workers scale by queue type.
- Alert ingestion scales separately from RCA execution.
- AI RCA is queued and rate-limited.
- Dashboard APIs can use caching for read-heavy workloads.

Data scaling:

- Partition or archive audit logs and alert history over time.
- Store long-term artifacts in S3.
- Keep operational summaries in PostgreSQL.
- Query high-cardinality telemetry from Prometheus and Loki rather than duplicating raw data.

## Reliability Model

Reliability controls:

- Idempotent alert ingestion
- Retry policies for transient integration failures
- Dead-letter handling for failed background jobs
- Provider timeouts and circuit breakers
- Manual approval for destructive remediation
- Audit-first design for sensitive actions
- Graceful degradation if AI providers are unavailable
- Health checks for every integration

## Multi-Tenancy Readiness

The initial design can run as single-tenant while keeping a path to multi-tenancy through:

- Tenant-scoped users, roles, services, clusters, integrations, incidents, and audit logs
- Tenant-aware repository filters
- Tenant-aware JWT claims
- Optional row-level security later
