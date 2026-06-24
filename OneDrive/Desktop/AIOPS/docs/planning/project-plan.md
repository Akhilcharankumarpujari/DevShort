# Project Plan

## Delivery Approach

The platform should be delivered in controlled phases. Each phase should produce a runnable, testable increment with clear acceptance criteria.

## Initial Scope

The first implementation milestone after approval should create the foundation only:

- Project scaffold
- Backend structure
- Frontend structure
- Local development setup
- Database baseline
- Health checks
- Documentation updates

Business features should be added only after the foundation is stable.

## Workstreams

### Backend Workstream

Responsibilities:

- FastAPI project setup
- Clean Architecture modules
- SQLAlchemy models and repositories
- Alembic migrations
- Auth and RBAC
- Incident and alert APIs
- Integration clients
- AI provider abstraction
- Remediation workflow
- Audit logging

### Frontend Workstream

Responsibilities:

- React/Vite setup
- Routing and layout
- Auth state
- API client layer
- Incident dashboard
- Alert views
- RCA views
- Remediation views
- Integration settings
- Admin and RBAC screens

### Infrastructure Workstream

Responsibilities:

- Docker setup
- Docker Compose for local development
- Kubernetes manifests
- Helm chart
- Terraform AWS modules
- Secrets management
- Environment configuration

### Observability Workstream

Responsibilities:

- Prometheus integration
- Alertmanager integration
- Loki integration
- Grafana dashboards and links
- Platform metrics
- Structured logs and tracing readiness

### Security Workstream

Responsibilities:

- JWT security
- RBAC policy model
- Secret redaction
- Secure integration storage
- Audit logging
- Dependency scanning
- Container scanning
- IAM least-privilege design

### AI Workstream

Responsibilities:

- OpenAI provider
- Ollama provider
- Prompt templates
- Context collection
- RCA output schema
- Sensitive data redaction
- AI usage auditing

## Suggested Milestones

| Milestone | Name | Outcome |
|---|---|---|
| M0 | Architecture approval | Documentation approved |
| M1 | Foundation | Runnable frontend/backend skeleton |
| M2 | Auth and RBAC | Secure user access |
| M3 | Incidents and alerts | Core incident workflows |
| M4 | Observability integrations | Metrics, logs, Kubernetes context |
| M5 | AI RCA | RCA generation and evidence reports |
| M6 | Remediation | Controlled action execution |
| M7 | AWS integration | Cloud context and CloudWatch signals |
| M8 | Production deployment | Docker, Kubernetes, Helm, CI/CD |
| M9 | Enterprise hardening | Advanced analytics, policies, multi-tenant readiness |

## Quality Gates

Each milestone should pass:

- Unit tests
- Integration tests for touched boundaries
- API schema validation
- Static analysis
- Formatting checks
- Security checks for changed dependencies
- Manual smoke test
- Documentation update

## Definition of Done

A feature is complete when:

- Backend API or worker logic is implemented
- Frontend workflow is implemented where applicable
- Permissions are enforced
- Audit logging exists for sensitive actions
- Tests cover expected success and failure paths
- Documentation is updated
- Local development instructions remain valid
- Deployment impact is understood

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| AI hallucinated RCA | Incorrect remediation decisions | Evidence-first RCA, confidence score, human approval |
| Overbroad remediation permissions | Production outage or security issue | RBAC, approval workflow, risk levels, audit logs |
| Secret exposure to AI providers | Compliance and security risk | Redaction layer, provider policies, audit metadata |
| Alert noise overload | Poor usability | Deduplication, correlation, suppression, routing policies |
| Integration instability | Partial platform degradation | Health checks, retries, timeouts, graceful degradation |
| Raw telemetry volume | Database growth and cost | Store summaries and references, not raw logs/metrics |
| AWS permissions too broad | Security exposure | Least-privilege IAM and external role assumptions |

## Approval Checkpoints

Approval should be requested before:

- Generating application source code
- Adding Dockerfiles and Kubernetes manifests
- Adding Terraform infrastructure
- Adding CI/CD pipelines
- Implementing auto-remediation execution
- Connecting to real external systems
