# Development Roadmap

## Phase 0: Architecture Approval

Status: current phase.

Deliverables:

- System architecture
- Folder structure
- Database design
- API design
- Architecture diagrams
- Development roadmap
- Project plan
- Documentation structure
- README

Exit criteria:

- Architecture approved
- Initial scope confirmed
- Implementation order approved

## Phase 1: Project Foundation

Goal: create the production-ready scaffold without business feature completion.

Deliverables:

- Backend FastAPI project structure
- Frontend React/Vite/TypeScript project structure
- Shared environment configuration approach
- Docker Compose for local dependencies
- PostgreSQL local setup
- Alembic baseline
- Basic health endpoints
- Initial linting and formatting configuration
- Baseline README updates

Exit criteria:

- Backend starts locally
- Frontend starts locally
- Database connection works
- Health checks pass
- No application feature logic beyond foundation

## Phase 2: Identity, Auth, and RBAC

Goal: secure the platform foundation.

Deliverables:

- User model
- Role and permission model
- JWT login and refresh flow
- Password hashing
- RBAC dependency checks
- Default roles: Admin, SRE, Developer, Viewer
- Protected frontend routes
- Admin user bootstrap process

Exit criteria:

- Users can authenticate
- Role permissions are enforced
- Admin can manage users and roles
- Security tests cover core permission paths

## Phase 3: Incident and Alert Management

Goal: deliver the operational core.

Deliverables:

- Incident CRUD and lifecycle transitions
- Incident timeline
- Alert source model
- Alert ingestion endpoint
- Alert normalization
- Alert deduplication
- Alert-to-incident linking
- Incident dashboard views

Exit criteria:

- Alerts can create or update incidents
- Incident status transitions are audited
- Frontend supports incident triage workflow

## Phase 4: Observability Integrations

Goal: connect operational telemetry.

Deliverables:

- Prometheus query integration
- Loki query integration
- Alertmanager webhook support
- Grafana deep links
- Kubernetes inventory integration
- Kubernetes events and workload views

Exit criteria:

- Incidents can display related metrics and logs
- Kubernetes workloads and events are visible
- Alertmanager can ingest alerts into the platform

## Phase 5: AI RCA

Goal: generate structured AI-assisted incident analysis.

Deliverables:

- AI provider abstraction
- OpenAI provider implementation
- Ollama provider implementation
- Prompt templates
- Context collector
- RCA report schema
- RCA request workflow
- Redaction before AI calls
- RCA UI inside incident detail

Exit criteria:

- User can run RCA for an incident
- RCA report includes summary, likely cause, evidence, confidence, and recommendations
- AI calls are audited and redact sensitive values

## Phase 6: Auto Remediation

Goal: support controlled remediation workflows.

Deliverables:

- Remediation action catalog
- Approval workflow
- Execution engine abstraction
- Kubernetes remediation actions
- Jenkins job trigger actions
- AWS operational actions
- Execution status tracking
- Remediation audit logs

Exit criteria:

- Low-risk actions can execute based on policy
- High-risk actions require approval
- Execution results are linked to incidents

## Phase 7: AWS Integration

Goal: enrich incidents with cloud infrastructure context.

Deliverables:

- AWS integration configuration
- IAM role support
- CloudWatch alarms and metrics
- EKS metadata
- EC2 metadata
- RDS metadata
- S3 artifact storage for RCA evidence bundles

Exit criteria:

- AWS resources can be discovered
- CloudWatch alerts can be correlated
- Incident evidence can include AWS resource context

## Phase 8: Dashboards and Analytics

Goal: provide operational visibility and leadership metrics.

Deliverables:

- Platform dashboard
- Incident trend analytics
- Alert noise analytics
- MTTA and MTTR analytics
- Remediation success analytics
- RCA usage analytics
- Service reliability views

Exit criteria:

- Users can track operational health from dashboards
- Metrics are filterable by service, cluster, severity, and time range

## Phase 9: Production Hardening

Goal: prepare for enterprise deployment.

Deliverables:

- Dockerfiles
- Kubernetes manifests
- Helm chart
- GitHub Actions pipelines
- Jenkins pipeline
- Security scanning
- Rate limiting
- Structured logging
- OpenTelemetry-ready tracing
- Backup and restore documentation
- Secrets management documentation

Exit criteria:

- Platform deploys through Helm
- CI validates backend, frontend, security, and container builds
- Production runbooks are available

## Phase 10: Enterprise Enhancements

Goal: expand enterprise readiness.

Deliverables:

- Multi-tenant model if required
- SLO and error budget views
- Notification routing
- Advanced correlation rules
- Post-incident review workflow
- Custom remediation plugins
- Policy-as-code integration

Exit criteria:

- Enterprise controls are implemented according to stakeholder priorities
