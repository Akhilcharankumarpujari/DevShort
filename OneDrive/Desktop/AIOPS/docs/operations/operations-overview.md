# Operations Overview

## Runtime Environments

Recommended environments:

- Local development
- Development
- Staging
- Production

Each environment should have separate configuration, secrets, database, and integration credentials.

## Production Runtime

Recommended production runtime:

- Kubernetes on AWS EKS
- PostgreSQL on AWS RDS
- Object storage on AWS S3
- Observability through Prometheus, Grafana, Alertmanager, Loki, and Promtail
- Backend and worker deployments scaled independently
- Frontend deployed as static assets or containerized web service

## Health Checks

The platform should expose:

- Liveness endpoint for process health
- Readiness endpoint for database and required dependency readiness
- Integration health endpoint for external systems

## Backup and Restore

Backup scope:

- PostgreSQL database
- S3 RCA artifacts and exports
- Helm values and deployment configuration
- Integration configuration metadata

Raw metrics and logs are governed by Prometheus and Loki retention or backup policies.

## Observability

The platform should emit:

- Structured application logs
- Request IDs
- Prometheus metrics
- Error counts
- Latency histograms
- Worker job metrics
- Integration health metrics
- RCA provider latency and failures
- Remediation execution metrics

## Platform Incident Response

The AIOps platform itself should have runbooks for:

- Backend API unavailable
- Database unavailable
- Alert ingestion delayed
- AI provider unavailable
- Remediation execution stuck
- Kubernetes integration failed
- AWS integration failed
