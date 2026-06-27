# TechHub – Cloud-Native Electronics & Computer Store

TechHub is a production-grade e-commerce application designed around a microservices architecture. This repository contains the Phase 1 implementation (architecture and infrastructure setup).

---

## 🏗️ Architecture & Component Layout

```text
techhub/
├── docker-compose.yml         # Production-like local orchestration
├── .gitignore
├── README.md                  # Workspace entry guide
├── api-gateway/               # FastAPI async HTTP routing gateway (Port 8000)
├── user-service/              # FastAPI User Profiles microservice (Port 8001)
├── product-service/           # FastAPI Catalog & Inventory specs (Port 8002)
├── order-service/             # FastAPI Checkout & Order flows (Port 8003)
├── inventory-service/         # FastAPI Stock allocations & location (Port 8004)
├── payment-service/           # FastAPI Charges and Ledger billing (Port 8005)
├── frontend/                  # Next.js 15 + TypeScript user app (Port 3000)
├── docker/                    # Live-reload compose structures for dev
├── kubernetes/                # Deployments, Services, ConfigMaps, Secrets, Ingress
├── monitoring/                # Prometheus metrics scrape configs & Grafana datasources
├── database/                  # PostgreSQL initial setup SQL multi-db schemas
└── docs/                      # Technical guides & system topology diagrams
```

Detailed design notes are available in the [docs/](file:///C:/Users/Manasa/.gemini/antigravity/scratch/techhub/docs) folder:
- [System Architecture](file:///C:/Users/Manasa/.gemini/antigravity/scratch/techhub/docs/architecture.md)
- [REST API Reference Guide](file:///C:/Users/Manasa/.gemini/antigravity/scratch/techhub/docs/api-guide.md)
- [Local Developer Setup](file:///C:/Users/Manasa/.gemini/antigravity/scratch/techhub/docs/development-setup.md)

---

## 🚀 Quick Start (Local Orchestration)

To spin up the entire cluster (Next.js, PostgreSQL, API Gateway, and 5 microservices):

```bash
docker compose up -d --build
```

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **API Gateway Swagger**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

To run in live-reload mode with mounted code directories:
```bash
docker compose -f docker/docker-compose.dev.yml up --build
```

---

## 🛠️ Infrastructure Features Included

* **Next.js 15 (App Router) & TypeScript**: Modern frontend template styled with Vanilla CSS and Custom Properties.
* **FastAPI Backend Services**: Structured, standardized Python boilerplate utilizing `pydantic-settings` to parse local environments.
* **Logging Configuration**: Structured, consistent logs configured with customizable formats.
* **PostgreSQL Integration**: Automated database bootstrapping script to create independent databases on initial container run.
* **Consolidated API Documentation**: Automatic Swagger/OpenAPI specifications exposed at `/api/v1/docs` for all services.
* **Health Checks**: Endpoint `/api/v1/health` checks service running status and verifies active DB connection pools.
* **Kubernetes Deployments**: Scalable manifest configurations with ConfigMaps, Secrets, Ingress mappings, and liveness/readiness check loops.
* **Prometheus Scraping Setup**: Configured jobs scraping from custom `/metrics` endpoints.
