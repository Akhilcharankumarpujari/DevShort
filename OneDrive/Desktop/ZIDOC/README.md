# Zidoc - AI-Powered Enterprise Document Lifecycle Platform

Zidoc is a production-grade, compliance-first document management platform designed to automate ingestion, extraction, and validation of enterprise credentials, articles, and agreements.

---

## Workspace Architecture

The repository utilizes a modular multi-language monorepo design layout:
- **`apps/api`**: Go backend modular monolith REST API (Gin, GORM, PostgreSQL, Redis, Swagger, Zap).
- **`apps/web`**: Single Page Application React frontend (React 19, TypeScript, Vite, Tailwind CSS, Zustand, Axios, TanStack Query).
- **`apps/ai-service`**: Microservice handling classification and extraction tasks (Python 3.11, FastAPI, pytest).
- **`deploy/`**: Configurations for Docker, Kubernetes (Kustomize), and Helm charts.
- **`packages/`**: Isolated local typescript types and shared config references.

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js v22 (local dev)
- Go v1.24+ (local dev)
- Python 3.11 (local dev)

### Spin Up Orchestration
To start the complete production-mimicking local ecosystem (DB, Redis, API, Frontend, AI Service):
```bash
docker compose up --build
```

---

## Telemetry & Ports Mapping

- **Go API Gateway**: `http://localhost:8080`
  - Health checks: `/health` (general), `/ready` (DB & Cache), `/live` (liveness)
  - Swagger Documentation: `/swagger/index.html`
- **React Frontend**: `http://localhost:5173`
- **FastAPI AI Service**: `http://localhost:8000`
  - Health checks: `/health` (general), `/live` (liveness)
- **PostgreSQL Database**: `localhost:5432`
- **Redis Cache Engine**: `localhost:6379`

---

## Complete Documentation Index

For detailed instructions and setups, please review our documentation files inside the `docs/` folder:
- [Architecture Details](docs/Architecture.md)
- [Development Walkthrough](docs/Development.md)
- [Workspace Folder Structure](docs/FolderStructure.md)
- [Step-by-step Local Setup](docs/Setup.md)
