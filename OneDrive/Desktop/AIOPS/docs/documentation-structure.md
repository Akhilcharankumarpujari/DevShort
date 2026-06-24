# Documentation Structure

## Overview

Documentation is organized by audience and operational need. Architecture docs explain the system design. API and database docs define contracts. Security and operations docs support production use. Runbooks support incident response.

## Structure

```text
docs/
  architecture/
    system-architecture.md
    folder-structure.md
    architecture-diagrams.md

  api/
    api-design.md
    auth.md
    rbac.md
    errors.md
    webhooks.md

  database/
    database-design.md
    migrations.md
    retention.md

  security/
    security-architecture.md
    authentication.md
    authorization.md
    secrets-management.md
    audit-logging.md
    ai-data-redaction.md
    aws-iam.md

  operations/
    operations-overview.md
    local-development.md
    docker.md
    kubernetes.md
    helm.md
    aws-deployment.md
    backup-restore.md
    monitoring.md

  runbooks/
    runbooks-index.md
    incident-management.md
    alert-triage.md
    ai-rca.md
    remediation-approval.md
    failed-integration.md
    database-restore.md

  roadmap/
    development-roadmap.md

  planning/
    project-plan.md
```

## Documentation Ownership

| Area | Primary Audience | Update Trigger |
|---|---|---|
| Architecture | Engineers, architects, leads | Architecture or dependency changes |
| API | Backend and frontend engineers | Endpoint contract changes |
| Database | Backend engineers, DB operators | Schema or retention changes |
| Security | Engineers, security reviewers | Auth, RBAC, secret, audit, or IAM changes |
| Operations | DevOps, SRE, platform engineers | Deployment or runtime changes |
| Runbooks | SRE and on-call engineers | Incident response workflow changes |
| Roadmap | Product and engineering leadership | Delivery plan changes |
| Planning | Project stakeholders | Scope or milestone changes |

## Documentation Rules

- Keep architecture decisions close to the system they affect.
- Update API docs whenever request or response contracts change.
- Update database docs whenever migrations change schema or retention.
- Update runbooks whenever operational behavior changes.
- Include security implications for AI, remediation, and integrations.
- Prefer diagrams for workflows that cross system boundaries.
