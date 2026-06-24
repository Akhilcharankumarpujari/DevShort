# Architecture Diagrams

## System Context

```mermaid
flowchart TB
  User["DevOps / SRE / Developer / Viewer"] --> Web["React Web App"]
  Web --> API["FastAPI Backend API"]
  API --> DB["PostgreSQL"]
  API --> Worker["Background Workers"]
  Worker --> DB
  API --> Prom["Prometheus"]
  API --> Loki["Loki"]
  API --> Grafana["Grafana"]
  API --> Alertmanager["Alertmanager"]
  API --> K8s["Kubernetes / EKS API"]
  API --> Jenkins["Jenkins"]
  API --> AWS["AWS APIs"]
  API --> AI["AI Provider Layer"]
  AI --> OpenAI["OpenAI API"]
  AI --> Ollama["Ollama"]
  Alertmanager --> API
  Jenkins --> API
  AWS --> API
```

## Clean Architecture Dependency Flow

```mermaid
flowchart LR
  UI["React Frontend"] --> API["API Routes"]
  API --> App["Application Use Cases"]
  Workers["Background Workers"] --> App
  App --> Domain["Domain Models and Services"]
  Infra["Infrastructure Adapters"] --> App
  Infra --> Domain
  Infra --> Postgres["PostgreSQL"]
  Infra --> External["External Systems"]
  Domain -. "No framework dependencies" .- Domain
```

## Backend Component View

```mermaid
flowchart TB
  Router["FastAPI Routers"] --> UseCases["Application Use Cases"]
  UseCases --> IncidentDomain["Incident Domain"]
  UseCases --> AlertDomain["Alert Domain"]
  UseCases --> RCADomain["RCA Domain"]
  UseCases --> RemediationDomain["Remediation Domain"]
  UseCases --> AuditDomain["Audit Domain"]
  UseCases --> Repositories["Repository Interfaces"]
  Repositories --> SQLA["SQLAlchemy Repositories"]
  SQLA --> PostgreSQL["PostgreSQL"]
  UseCases --> ProviderInterfaces["Provider Interfaces"]
  ProviderInterfaces --> PromClient["Prometheus Client"]
  ProviderInterfaces --> LokiClient["Loki Client"]
  ProviderInterfaces --> K8sClient["Kubernetes Client"]
  ProviderInterfaces --> JenkinsClient["Jenkins Client"]
  ProviderInterfaces --> AWSClient["AWS Client"]
  ProviderInterfaces --> AIClient["AI Provider Client"]
```

## Alert to Incident Workflow

```mermaid
sequenceDiagram
  participant Source as Alert Source
  participant API as Alert Ingestion API
  participant AlertSvc as Alert Service
  participant Corr as Correlation Engine
  participant Inc as Incident Service
  participant DB as PostgreSQL
  participant Audit as Audit Service

  Source->>API: Send alert payload
  API->>AlertSvc: Validate and normalize
  AlertSvc->>DB: Upsert alert
  AlertSvc->>Corr: Correlate alert
  Corr->>DB: Search active incidents
  alt Matching incident exists
    Corr->>Inc: Link alert to incident
    Inc->>DB: Add incident event
  else No matching incident
    Corr->>Inc: Create incident
    Inc->>DB: Persist incident
  end
  Inc->>Audit: Record workflow event
  Audit->>DB: Write audit log
```

## AI RCA Workflow

```mermaid
sequenceDiagram
  participant User as User
  participant API as RCA API
  participant RCA as RCA Service
  participant Ctx as Context Collector
  participant Prom as Prometheus
  participant Loki as Loki
  participant K8s as Kubernetes
  participant Jenkins as Jenkins
  participant AWS as AWS
  participant AI as AI Provider
  participant DB as PostgreSQL

  User->>API: Request RCA for incident
  API->>RCA: Start analysis
  RCA->>Ctx: Gather incident context
  Ctx->>Prom: Query metrics
  Ctx->>Loki: Query logs
  Ctx->>K8s: Query events and workload state
  Ctx->>Jenkins: Query deployment/build history
  Ctx->>AWS: Query CloudWatch/resource metadata
  Ctx-->>RCA: Return summarized evidence
  RCA->>AI: Generate structured RCA
  AI-->>RCA: RCA result
  RCA->>DB: Save RCA report
  RCA-->>API: Return report status
  API-->>User: RCA report response
```

## Remediation Workflow

```mermaid
flowchart LR
  RCA["RCA Report"] --> Suggest["Recommended Actions"]
  User["Authorized User"] --> Select["Select Action"]
  Select --> Policy["Policy and RBAC Check"]
  Policy --> Risk{"Requires Approval?"}
  Risk -- Yes --> Approval["Approval Workflow"]
  Risk -- No --> Execute["Execution Engine"]
  Approval --> Execute
  Execute --> Target{"Target Provider"}
  Target --> K8s["Kubernetes"]
  Target --> Jenkins["Jenkins"]
  Target --> AWS["AWS"]
  Target --> Manual["Manual Runbook"]
  Execute --> Result["Execution Result"]
  Result --> Timeline["Incident Timeline"]
  Result --> Audit["Audit Log"]
```

## Deployment Architecture

```mermaid
flowchart TB
  Internet["Users"] --> Ingress["Kubernetes Ingress"]
  Ingress --> FrontendSvc["Frontend Service"]
  Ingress --> BackendSvc["Backend API Service"]
  BackendSvc --> BackendPods["FastAPI Pods"]
  BackendPods --> RDS["AWS RDS PostgreSQL"]
  BackendPods --> Queue["Worker Queue"]
  Queue --> WorkerPods["Worker Pods"]
  WorkerPods --> RDS
  BackendPods --> Prom["Prometheus"]
  BackendPods --> Loki["Loki"]
  BackendPods --> Alertmanager["Alertmanager"]
  BackendPods --> S3["AWS S3"]
  BackendPods --> CloudWatch["AWS CloudWatch"]
  BackendPods --> EKS["AWS EKS / Kubernetes API"]
  BackendPods --> Jenkins["Jenkins"]
  BackendPods --> AI["OpenAI / Ollama"]
  Grafana["Grafana"] --> Prom
  Grafana --> Loki
```

## Database Relationship Diagram

```mermaid
erDiagram
  USERS ||--o{ USER_ROLES : has
  ROLES ||--o{ USER_ROLES : maps
  ROLES ||--o{ ROLE_PERMISSIONS : grants
  PERMISSIONS ||--o{ ROLE_PERMISSIONS : maps
  SERVICES ||--o{ INCIDENTS : affected_by
  SERVICES ||--o{ ALERTS : emits
  SERVICES ||--o{ WORKLOADS : owns
  CLUSTERS ||--o{ NAMESPACES : contains
  NAMESPACES ||--o{ WORKLOADS : contains
  CLUSTERS ||--o{ INCIDENTS : relates_to
  CLUSTERS ||--o{ ALERTS : relates_to
  ALERT_SOURCES ||--o{ ALERTS : produces
  ALERTS ||--o{ INCIDENT_ALERTS : linked_to
  INCIDENTS ||--o{ INCIDENT_ALERTS : includes
  INCIDENTS ||--o{ INCIDENT_EVENTS : has
  INCIDENTS ||--o{ RCA_REPORTS : analyzed_by
  INCIDENTS ||--o{ METRICS_SNAPSHOTS : has
  INCIDENTS ||--o{ LOG_FINDINGS : has
  INCIDENTS ||--o{ REMEDIATION_EXECUTIONS : remediated_by
  REMEDIATION_ACTIONS ||--o{ REMEDIATION_EXECUTIONS : executes
  USERS ||--o{ AUDIT_LOGS : creates
```

## Frontend Information Architecture

```mermaid
flowchart TB
  App["AIOps Platform"] --> Dashboard["Dashboard"]
  App --> Incidents["Incidents"]
  App --> Alerts["Alerts"]
  App --> Kubernetes["Kubernetes"]
  App --> Metrics["Metrics"]
  App --> Logs["Logs"]
  App --> RCA["AI RCA"]
  App --> Remediation["Remediation"]
  App --> Integrations["Integrations"]
  App --> Audit["Audit Logs"]
  App --> Admin["Admin"]
  Incidents --> IncidentDetail["Incident Detail"]
  IncidentDetail --> Timeline["Timeline"]
  IncidentDetail --> Evidence["Evidence"]
  IncidentDetail --> RCAReport["RCA Report"]
  IncidentDetail --> Remediate["Remediation"]
```
