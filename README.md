# DevShort

A modern, production-ready URL Shortener with QR Code generation and click analytics.

<!-- BADGES -->
[![CI](https://github.com/Akhilcharankumarpujari/DevShort/actions/workflows/ci.yml/badge.svg)](https://github.com/Akhilcharankumarpujari/DevShort/actions/workflows/ci.yml)
[![Deploy](https://github.com/Akhilcharankumarpujari/DevShort/actions/workflows/deploy.yml/badge.svg)](https://github.com/Akhilcharankumarpujari/DevShort/actions/workflows/deploy.yml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=nodedotjs&logoColor=white)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Tech Stack

| Layer      | Technology                                     |
| ---------- | ---------------------------------------------- |
| Frontend   | React 19, Vite, Tailwind CSS, Axios            |
| Backend    | Node.js, Express.js, Prisma ORM, NanoID        |
| Database   | PostgreSQL 16                                  |
| DevOps     | Docker, Docker Compose, GitHub Actions         |
| Monitoring | Prometheus, Grafana, CloudWatch                |

---

## CI/CD Pipeline Overview

The project uses **GitHub Actions** for continuous integration and deployment:

| Pipeline | Workflow File | Trigger |
| -------- | ------------- | ------- |
| **CI**   | `.github/workflows/ci.yml` | Every `push` and `pull_request` on `main` |
| **CD**   | `.github/workflows/deploy.yml` | After successful CI on `main`, or manual dispatch |

---

## Continuous Integration (CI)

```mermaid
graph TD
    A[push / PR] --> B[Checkout]
    B --> C[Backend CI]
    B --> D[Frontend CI]
    C --> C1[Install Dependencies]
    C1 --> C2[Generate Prisma Client]
    C2 --> C3[Validate Prisma Schema]
    C3 --> C4[Verify Entry Point]
    D --> D1[Install Dependencies]
    D1 --> D2[Vite Production Build]
    D2 --> D3[Verify Build Output]
    C4 --> E[Docker CI]
    D3 --> E
    E --> E1[Verify Dockerfiles]
    E1 --> E2[Validate docker-compose.yml]
    E2 --> E3[Build Docker Images]
    E3 --> F[Success Summary]
```

### CI Stages

| # | Stage | Description |
| - | ----- | ----------- |
| 1 | **Backend CI** | Installs dependencies, generates Prisma client, validates schema, verifies entry point |
| 2 | **Frontend CI** | Installs dependencies, runs Vite production build, verifies `dist/` output |
| 3 | **Docker CI** | Lints Dockerfiles, validates `docker-compose.yml`, builds all images |
| 4 | **Summary** | Reports final pipeline status — ready for deployment or failed |

### Key CI Features

- **Parallel execution** — Backend and Frontend jobs run concurrently
- **npm caching** — `node_modules` cached per `package-lock.json` hash
- **Docker layer caching** — BuildKit cache for faster Docker builds
- **Fail fast** — Any failing step stops the pipeline immediately
- **Concurrency groups** — Auto-cancels redundant runs on the same branch

---

## Continuous Deployment (CD)

```mermaid
graph TD
    A[CI Passes on main] --> B[Pre-Deploy Check]
    B --> C[Build Docker Images]
    C --> D[Transfer to EC2]
    D --> E[Stop Existing Containers]
    E --> F[docker compose up -d --build]
    F --> G[Wait for PostgreSQL]
    G --> H[Run Prisma Migration]
    H --> I[Verify Backend Health]
    I --> J[Verify Frontend]
    J --> K[Verify Database]
    K --> L[Deployment Success]
    
    F -.->|On Failure| R[Rollback]
    R --> R1[Stop Failed Containers]
    R1 --> R2[Restore Previous Images]
    R2 --> R3[Restart Services]
    R3 --> R4[Post-Rollback Health Check]
    R4 --> R5[Generate Rollback Log]
```

### CD Stages

| # | Stage | Description |
| - | ----- | ----------- |
| 1 | **Pre-Deploy Check** | Validates branch, verifies all required secrets are set |
| 2 | **Build Images** | Builds backend + frontend Docker images, uploads as artifacts |
| 3 | **Transfer** | Copies images, configs, and Prisma schema to EC2 via SCP |
| 4 | **Backup** | Tags current running images as `:previous` for rollback |
| 5 | **Stop & Deploy** | Stops existing containers, starts new ones with `docker compose up -d` |
| 6 | **Migration** | Runs `npx prisma migrate deploy` inside the backend container |
| 7 | **Health Checks** | Verifies backend `GET /api/health` returns 200 |
| 8 | **Frontend Check** | Verifies frontend serves HTTP 200 |
| 9 | **Database Check** | Runs `pg_isready` to confirm DB connectivity |
| 10 | **Rollback** (on failure) | Stops failed deployment, restores `:previous` images, health-checks restored version |

### Rollback Behavior

If any deployment step fails:

1. The failed containers are stopped
2. Previous working images (tagged `:previous`) are restored
3. Services are restarted with the previous version
4. A post-rollback health check verifies the restoration
5. A timestamped rollback log is written to `~/devshort/logs/`

---

## Quick Start

### Prerequisites

- **Node.js 22+** (or latest LTS)
- **Docker & Docker Compose**
- **PostgreSQL 16** (if running locally without Docker)

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

- **Frontend:** http://localhost:5173
- **Backend:**  http://localhost:4000

### Local Development

**Backend:**

```bash
cd backend
cp ../.env.example .env
# Update DATABASE_URL to point to localhost
npm install
npx prisma generate
npx prisma db push
npm run dev
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## GitHub Secrets Setup

The CD pipeline requires these secrets configured in your GitHub repository.

> **Navigate to:** GitHub → Repository → Settings → Secrets and variables → Actions

### Required Secrets

| Secret | Description | Example |
| ------ | ----------- | ------- |
| `EC2_HOST` | AWS EC2 instance public IP or DNS | `ec2-13-52-1-123.compute-1.amazonaws.com` |
| `EC2_USERNAME` | SSH username for EC2 | `ec2-user` (Amazon Linux) or `ubuntu` |
| `EC2_SSH_KEY` | Private SSH key for EC2 access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DATABASE_URL` | Production PostgreSQL connection URL | `postgresql://user:pass@host:5432/devshort` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `your-secure-password` |

### Optional Secrets

| Secret | Description |
| ------ | ----------- |
| `JWT_SECRET` | Secret key for JWT token signing (if auth is added) |
| `PORT` | Custom backend port (default: `4000`) |

### Optional Variables

| Variable | Description |
| -------- | ----------- |
| `APP_URL` | Public URL of your application (used in health checks and CORS) |

### Setting Up EC2 SSH Key

```bash
# Generate an SSH key pair (on your local machine)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/devshort-deploy

# Copy the public key to your EC2 instance
ssh-copy-id -i ~/.ssh/devshort-deploy.pub ec2-user@your-ec2-host

# Add the PRIVATE key as a GitHub secret
# Copy the output of:
cat ~/.ssh/devshort-deploy
# → Paste into GitHub Secret: EC2_SSH_KEY
```

---

## Deployment Flow

### Full Deployment Pipeline

```
Developer pushes to main
        │
        ▼
┌──────────────────┐
│  CI Pipeline     │
│  · Backend       │
│  · Frontend      │
│  · Docker        │
└──────┬───────────┘
       │ CI passes
       ▼
┌──────────────────┐
│  CD Pipeline     │
│  · Build images  │
│  · Transfer to   │
│    EC2           │
│  · Stop old      │
│  · Start new     │
│  · Migrate DB    │
│  · Health check  │
└──────┬───────────┘
       │
   ┌───┴───┐
   │       │
 Success  Failure
   │       │
   ▼       ▼
  Live   Rollback
```

### Manual Deployment

1. Go to **Actions** → **DevShort Continuous Deployment**
2. Click **Run workflow**
3. Select environment (`production` or `staging`)
4. Click **Run workflow**

### Checking Deployment Status

```bash
# On EC2, check running containers
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Check backend health
curl http://localhost:4000/api/health
```

---

## API Reference

### Shorten a URL

```
POST /api/urls
Content-Type: application/json

{ "url": "https://example.com/very-long-url" }

Response 201:
{
  "data": {
    "id": "clx...",
    "originalUrl": "https://example.com/very-long-url",
    "shortCode": "aB3xK9mQ",
    "shortUrl": "http://localhost:4000/aB3xK9mQ",
    "clickCount": 0,
    "createdAt": "2026-07-08T12:00:00.000Z",
    "lastClickedAt": null
  }
}
```

### Redirect to Original URL

```
GET /:shortCode

Response: 302 Redirect to original URL
```

### Health Check

```
GET /api/health

Response 200:
{ "status": "ok", "timestamp": "2026-07-08T12:00:00.000Z" }
```

---

## Environment Variables

| Variable            | Description              | Default                                                |
| ------------------- | ------------------------ | ------------------------------------------------------ |
| `POSTGRES_USER`     | PostgreSQL user          | `devshort`                                             |
| `POSTGRES_PASSWORD` | PostgreSQL password      | `devshort_pass`                                        |
| `POSTGRES_DB`       | PostgreSQL database      | `devshort`                                             |
| `DATABASE_URL`      | Prisma connection URL    | `postgresql://devshort:devshort_pass@postgres:5432/devshort` |
| `PORT`              | Backend port             | `4000`                                                 |
| `SHORT_CODE_LENGTH` | Short code length        | `8`                                                    |
| `BASE_URL`          | Base URL for short URLs  | `http://localhost:4000`                                |
| `CORS_ORIGIN`       | Allowed CORS origin      | `http://localhost:5173`                                |
| `VITE_API_URL`      | Frontend API URL         | `http://localhost:4000`                                |

---

## Running Workflows Locally

While GitHub Actions runs in the cloud, you can validate workflows locally:

```bash
# Install act (GitHub Actions local runner)
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI workflow locally
act push -W .github/workflows/ci.yml

# Run specific job
act -j backend-ci -W .github/workflows/ci.yml
```

---

## Troubleshooting

### CI Pipeline

| Issue | Solution |
| ----- | -------- |
| **Prisma generate fails** | Run `npx prisma generate` locally to check for schema errors |
| **Vite build fails** | Check `frontend/src/` for import errors; run `npm run build` locally |
| **Docker build fails** | Verify `Dockerfile` paths; ensure `package-lock.json` is committed |
| **Cache not hitting** | Check that `package-lock.json` hash matches; clear cache in Actions tab |
| **npm ci fails** | Delete `node_modules` and `package-lock.json`, run `npm install` to regenerate |

### CD Pipeline

| Issue | Solution |
| ----- | -------- |
| **SSH connection refused** | Verify `EC2_HOST` is reachable; check security group allows port 22 |
| **Permission denied (publickey)** | Ensure `EC2_SSH_KEY` is the *private* key matching the EC2 instance's `~/.ssh/authorized_keys` |
| **Docker not found on EC2** | Install Docker on EC2: `sudo yum install -y docker` or `sudo apt install -y docker.io` |
| **Prisma migration fails** | SSH into EC2 and run `docker compose exec backend npx prisma migrate status` |
| **Health check timeout** | Check backend logs: `docker compose logs backend`; verify DATABASE_URL is correct |
| **Rollback fails** | Manually restore: `docker tag devshort-backend:previous devshort-backend:latest && docker compose up -d` |

### GitHub Actions

| Issue | Solution |
| ----- | -------- |
| **Workflow not triggering** | Check `.github/workflows/` files are on the correct branch |
| **Secrets not available** | Secrets are not passed to forks; they must be set in the upstream repo |
| **Runner out of disk space** | Use `actions/cache` to reduce install times; clean up old artifacts |

---

## Project Structure

```
devshort/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Continuous Integration pipeline
│       └── deploy.yml          # Continuous Deployment pipeline
├── backend/
│   ├── prisma/
│   │   └── schema.prisma       # Database schema
│   ├── src/
│   │   ├── config/             # App configuration
│   │   ├── controllers/        # Route handlers
│   │   ├── lib/                # Prisma client singleton
│   │   ├── middleware/         # Express middleware
│   │   ├── routes/             # API route definitions
│   │   ├── services/           # Business logic
│   │   ├── utils/              # Utilities (NanoID, errors)
│   │   ├── app.js              # Express app setup
│   │   └── index.js            # Server entry point
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── wait-for-db.cjs
│   └── package.json
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── lib/                # API client, utilities
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Phase 1 Scope

- [x] Project scaffolding (monorepo structure)
- [x] PostgreSQL + Prisma ORM setup
- [x] URL shortening endpoint (POST /api/urls)
- [x] URL redirect with click tracking (GET /:shortCode)
- [x] Health check endpoint (GET /api/health)
- [x] Frontend shell (Hero, feature cards, CTA section)
- [x] Docker Compose orchestration
- [x] Rate limiting on API routes
- [x] Security middleware (Helmet, CORS)

## Phase 2 & 3 — CI/CD (Current)

- [x] GitHub Actions CI pipeline (`ci.yml`)
- [x] GitHub Actions CD pipeline (`deploy.yml`)
- [x] Parallel backend + frontend CI jobs
- [x] Docker image validation & building
- [x] EC2 deployment with health checks
- [x] Automatic rollback on deployment failure
- [x] Prisma migration in deployment
- [x] GitHub Secrets documentation
- [x] CI/CD badges in README

## Remaining Work Before AWS Deployment

| # | Task | Details |
| - | ---- | ------- |
| 1 | **Provision EC2 Instance** | Launch EC2 (t3.small+), install Docker, Docker Compose, and Node.js 22 |
| 2 | **Configure Security Groups** | Open ports: `22` (SSH), `80` (HTTP), `443` (HTTPS), `4000` (API) |
| 3 | **Set Up RDS (PostgreSQL)** | Create RDS PostgreSQL 16 instance, configure VPC + security groups |
| 4 | **Set Up ECR (Optional)** | Create ECR repositories for `devshort-backend` and `devshort-frontend` |
| 5 | **Add GitHub Secrets** | Set all required secrets in GitHub Actions (see [GitHub Secrets Setup](#github-secrets-setup)) |
| 6 | **Configure Domain & SSL** | Point domain to EC2, set up Nginx reverse proxy with Let's Encrypt SSL |
| 7 | **Set Up CloudWatch** | Configure CloudWatch agent on EC2 for logs and metrics |
| 8 | **Configure Prometheus & Grafana** | Set up monitoring dashboards for backend health, latency, and DB metrics |
| 9 | **Run Smoke Tests** | Deploy manually first, test API endpoints, verify redirects work |
| 10 | **Enable Auto-Deploy** | Push to `main` and verify the full CI → CD pipeline works end-to-end |
