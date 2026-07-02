# Project Folder Layout Directory

Below is the directory structure layout for Phase 1.

```
ZIDOC/
├── .github/
│   └── workflows/
│       └── ci.yml             # Github Actions continuous integration workflow
├── apps/
│   ├── ai-service/            # FastAPI service (python 3.11, pytest, Dockerfile)
│   │   ├── main.py
│   │   ├── test_main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── api/                   # Go modular API (Gin, GORM, Postgres/Redis pools)
│   │   ├── cmd/               # Bootstrappers
│   │   ├── docs/              # Pre-compiled Swagger configurations
│   │   ├── internal/          # Layers (Handlers, Middlewares, Routers)
│   │   ├── migrations/        # golang-migrate database baselines
│   │   ├── pkg/               # Database, Redis, Logger configs
│   │   ├── Dockerfile
│   │   ├── config.yaml
│   │   └── go.mod
│   └── web/                   # Vite frontend application (React 19, TypeScript)
│       ├── src/
│       │   ├── components/    # Layout, Sidebar, Navbar, ErrorBoundary
│       │   ├── context/       # Theme transitions
│       │   ├── lib/           # Axios instance configurations
│       │   ├── pages/         # LandingPage, Dashboard, NotFound
│       │   ├── store/         # Zustand global states
│       │   └── test/          # Setup matchers
│       ├── Dockerfile
│       ├── tailwind.config.js
│       └── vite.config.ts
├── deploy/
│   ├── kubernetes/
│   │   ├── base/              # Common deployments & services
│   │   └── overlays/
│   │       ├── dev/           # Development environment overrides
│   │       └── prod/          # Production replica scale overrides
│   └── helm/                  # Chart setup for multi-service deployments
│       ├── Chart.yaml
│       └── values.yaml
├── docs/                      # Architectural & setup walkthrough manuals
├── packages/                  # Shareable configurations and typescript type files
├── docker-compose.yml         # Container coordinator
└── README.md                  # Main entrypoint index manual
```
