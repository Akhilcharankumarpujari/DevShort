# Security Architecture

## Security Goals

- Protect operational control surfaces.
- Prevent unauthorized remediation actions.
- Preserve auditability of privileged workflows.
- Avoid leaking secrets or sensitive telemetry to AI providers.
- Enforce least privilege across users, Kubernetes, and AWS.

## Authentication

- JWT access tokens for API calls.
- Refresh tokens for session continuity.
- Passwords stored with a strong adaptive hash.
- Authentication endpoints rate-limited.
- Token expiry configured by environment.

## Authorization

Authorization is role-based with granular permissions.

Built-in roles:

- Admin
- SRE
- Developer
- Viewer

Authorization should be enforced at endpoint level and object level for incidents, services, clusters, and integrations.

## Secret Management

Secrets must not be committed to source control.

Secrets include:

- JWT signing keys
- Database passwords
- OpenAI API keys
- Jenkins tokens
- AWS credentials or role references
- Kubernetes credentials
- Webhook tokens

Production storage options:

- AWS Secrets Manager
- Kubernetes Secrets with encryption at rest
- External Secrets Operator
- Vault, if introduced later

## AI Data Protection

Before sending context to OpenAI or another external AI provider:

- Redact API keys, tokens, passwords, private keys, and credentials.
- Redact personally sensitive data where possible.
- Truncate excessive logs.
- Preserve evidence references in the platform database.
- Store provider, model, token usage, and prompt version metadata.

Ollama may be used for local/private model execution where data residency is required.

## Remediation Safety

Controls:

- Risk level per action
- Allowed roles per action
- Required approval for medium, high, or critical actions
- Execution parameter validation
- Immutable audit logging
- Incident timeline updates
- Clear success/failure result capture

## AWS Security

AWS access should use IAM roles wherever possible.

Principles:

- Least-privilege policies
- Separate roles per environment
- No long-lived credentials in source control
- CloudTrail enabled outside this platform
- S3 buckets encrypted
- RDS encrypted
- EKS access scoped by role

## Kubernetes Security

Kubernetes access should use scoped service accounts.

Controls:

- Namespace-scoped permissions where possible
- Separate read-only and remediation service accounts
- No cluster-admin permission for normal operation
- Kubernetes Secrets protected through cluster policy
- Network policies where supported

## Audit Events

Audit logs should be recorded for:

- Login attempts
- User and role changes
- Integration configuration changes
- Alert source changes
- Incident lifecycle changes
- RCA requests
- AI provider call metadata
- Remediation approvals
- Remediation executions
- Failed permission checks for sensitive actions
