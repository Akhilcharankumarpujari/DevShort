# Folder Structure

This document defines the intended production folder structure. Only documentation is generated at the current checkpoint. Source code, manifests, Dockerfiles, Helm charts, CI/CD pipelines, and infrastructure code should be created only after approval.

```text
AIOPS/
  README.md
  .env.example
  .gitignore

  frontend/
    package.json
    vite.config.ts
    tsconfig.json
    tailwind.config.ts
    components.json
    public/
    src/
      app/
        App.tsx
        providers.tsx
        router.tsx
      assets/
      components/
        ui/
        layout/
        charts/
        forms/
        status/
      features/
        auth/
        dashboard/
        incidents/
        alerts/
        kubernetes/
        metrics/
        logs/
        rca/
        remediation/
        integrations/
        audit-logs/
        admin/
      hooks/
      lib/
      routes/
      services/
      stores/
      styles/
      types/
      tests/

  backend/
    pyproject.toml
    alembic.ini
    app/
      main.py
      api/
        deps.py
        errors.py
        v1/
          router.py
          auth.py
          users.py
          roles.py
          incidents.py
          alerts.py
          kubernetes.py
          metrics.py
          logs.py
          rca.py
          remediation.py
          integrations.py
          audit_logs.py
          dashboards.py
      core/
        config.py
        logging.py
        telemetry.py
        exceptions.py
      domain/
        identity/
        incidents/
        alerts/
        observability/
        rca/
        remediation/
        integrations/
        audit/
      application/
        identity/
        incidents/
        alerts/
        observability/
        rca/
        remediation/
        integrations/
        audit/
        dashboards/
      infrastructure/
        db/
        repositories/
        security/
        ai/
        kubernetes/
        prometheus/
        loki/
        alertmanager/
        grafana/
        jenkins/
        aws/
        notifications/
        queues/
      schemas/
      workers/
      observability/
      tests/
        unit/
        integration/
        contract/
    alembic/
      versions/
    scripts/

  infra/
    docker/
      backend.Dockerfile
      frontend.Dockerfile
      worker.Dockerfile
      docker-compose.yml
    kubernetes/
      namespace.yaml
      backend-deployment.yaml
      frontend-deployment.yaml
      worker-deployment.yaml
      services.yaml
      ingress.yaml
      configmaps.yaml
      secrets.example.yaml
    helm/
      aiops-platform/
        Chart.yaml
        values.yaml
        templates/
    terraform/
      aws/
        environments/
          dev/
          staging/
          prod/
        modules/
          eks/
          rds/
          s3/
          iam/
          monitoring/

  monitoring/
    prometheus/
      prometheus.yml
      rules/
    grafana/
      dashboards/
      provisioning/
    alertmanager/
      alertmanager.yml
      templates/
    loki/
      loki-config.yaml
    promtail/
      promtail-config.yaml

  cicd/
    github-actions/
      ci.yml
      security.yml
      deploy.yml
    jenkins/
      Jenkinsfile
      jobs/

  docs/
    architecture/
    api/
    database/
    security/
    operations/
    runbooks/
    roadmap/
    planning/

  scripts/
    dev/
    db/
    deploy/
    maintenance/
```

## Responsibilities

### frontend

Contains the React/Vite user interface. Feature folders should own their screens, hooks, components, route metadata, and API bindings where practical.

### backend

Contains the FastAPI backend. The backend is organized by Clean Architecture layers and domain boundaries.

### infra

Contains deployment and infrastructure artifacts, including Docker, Kubernetes, Helm, and Terraform definitions.

### monitoring

Contains Prometheus, Grafana, Alertmanager, Loki, and Promtail configuration.

### cicd

Contains GitHub Actions and Jenkins pipeline definitions.

### docs

Contains architecture, API, database, security, operations, runbooks, roadmap, and planning documents.

### scripts

Contains developer, database, deployment, and maintenance scripts.

## Backend Layering Rules

- `domain` must not import from `infrastructure`, `api`, or framework-specific modules.
- `application` may depend on `domain` interfaces and orchestrate use cases.
- `infrastructure` implements interfaces defined by domain or application layers.
- `api` maps HTTP requests into application use cases.
- `schemas` contains Pydantic request and response models.
- `workers` should call application use cases rather than directly manipulating repositories.

## Frontend Organization Rules

- Shared UI primitives live under `components/ui`.
- Layout components live under `components/layout`.
- Feature-specific screens and logic live under `features`.
- API clients live under `services`.
- Shared domain types live under `types`.
- React Query hooks may live inside feature folders when feature-specific.

## Naming Conventions

- Backend modules use snake_case.
- Frontend components use PascalCase.
- Frontend hooks use camelCase with `use` prefix.
- Database tables use plural snake_case names.
- API paths use kebab-case where needed, with version prefix `/api/v1`.
