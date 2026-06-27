# Local Development Setup Guide

This document guides engineers on setting up the local workspace.

## Prerequisites

Ensure you have the following installed:
1. **Docker & Docker Compose** (v2.0 or higher)
2. **Python 3.10+** (if running services bare-metal)
3. **Node.js 18+ & npm** (if running frontend bare-metal)

---

## 1. Running the Orchestration Stack

The quickest way to boot the full cloud-native stack is via Docker Compose:

```bash
# Build and run all services in detached mode
docker compose up -d --build
```

### Checking Services Status
Verify containers are running:
```bash
docker compose ps
```

To view live application logs:
```bash
docker compose logs -f [service-name]
```

---

## 2. Dev Live Reload Mode (Development)

To enable live code changes and hot reloading for development, use the development compose configuration:

```bash
# From the root directory
docker compose -f docker/docker-compose.dev.yml up --build
```
This runs:
- FastAPI with `--reload` flag enabled.
- Next.js with `npm run dev` watcher.
- Root folder volume bindings allowing instant code synchronization.

---

## 3. Environment Variables Configuration

Each service manages configuration using a local `.env` file (copied from `.env.example`).

To manually adjust ports or database URLs:
- **FastAPI**: Loaded natively via Python `pydantic-settings`. Define variables in `<service-folder>/.env`.
- **Frontend**: Managed via Next.js default environment configuration in `frontend/.env.local`.
