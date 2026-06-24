# AIOps Platform

Enterprise-grade AI-Powered DevOps and SRE platform for incident management, alert management, Kubernetes monitoring, log analysis, metrics analysis, AI root cause analysis, Jenkins integration, AWS integration, auto remediation, audit logging, and dashboard analytics.

Current implementation status: architecture documentation, backend foundation, and backend authentication/RBAC are generated. Frontend, incident domain features, observability integrations, infrastructure manifests, Helm charts, Terraform, and CI/CD pipelines are not generated yet.

## Objective

Build a production-ready AIOps platform that helps DevOps and SRE teams detect, analyze, troubleshoot, and remediate infrastructure and application incidents using AI-assisted workflows.

## Core Capabilities

- Incident lifecycle management
- Alert ingestion, normalization, deduplication, and correlation
- Kubernetes and EKS observability
- Metrics analysis through Prometheus
- Log analysis through Loki
- AI root cause analysis using OpenAI and Ollama providers
- Jenkins and CI/CD incident correlation
- AWS infrastructure visibility through CloudWatch, EC2, RDS, EKS, S3, and IAM integrations
- Controlled auto remediation workflows
- RBAC-secured operations
- Audit logging for security and compliance
- Dashboards for operational analytics

## Technology Stack

Frontend: React, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Query, Axios, React Router.

Backend: FastAPI, Python 3.12, SQLAlchemy 2.0, Alembic, Pydantic v2.

Database: PostgreSQL.

Authentication: JWT authentication with RBAC for Admin, SRE, Developer, and Viewer roles.

AI: OpenAI API and Ollama support through a provider abstraction.

Monitoring and logging: Prometheus, Grafana, Alertmanager, Loki, and Promtail.

Infrastructure and delivery: Docker, Kubernetes, Helm, GitHub Actions, Jenkins, and AWS.

## Generated Backend Capabilities

The backend lives in [`backend`](backend/).

Included backend capabilities:

- FastAPI application setup
- Configuration management with Pydantic Settings
- Structured JSON logging with request IDs
- Async SQLAlchemy PostgreSQL connection
- Alembic migration environment
- Health check APIs
- Global exception handling
- JWT authentication
- Refresh-token rotation and logout revocation
- Password hashing
- RBAC roles and permissions
- Authorization middleware and route dependencies
- Production Dockerfile
- Unit tests for health, password hashing, tokens, schemas, and RBAC

## Architecture Principles

- Clean Architecture
- Domain Driven Design
- SOLID principles
- Separation of concerns
- Secure-by-default design
- Auditable operational workflows
- Provider abstraction for external systems
- Infrastructure-agnostic core domain logic
- Production-grade observability and deployment practices

## Documentation Index

- [System Architecture](docs/architecture/system-architecture.md)
- [Folder Structure](docs/architecture/folder-structure.md)
- [Architecture Diagrams](docs/architecture/architecture-diagrams.md)
- [Database Design](docs/database/database-design.md)
- [API Design](docs/api/api-design.md)
- [Development Roadmap](docs/roadmap/development-roadmap.md)
- [Project Plan](docs/planning/project-plan.md)
- [Documentation Structure](docs/documentation-structure.md)
- [Security Architecture](docs/security/security-architecture.md)
- [Operations Overview](docs/operations/operations-overview.md)
- [Runbooks Index](docs/runbooks/runbooks-index.md)

## Backend Quick Start

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Health endpoints:

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

Auth endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

## Next Approval Gate

Next implementation step after approval: build the incident and alert management domain foundation.
