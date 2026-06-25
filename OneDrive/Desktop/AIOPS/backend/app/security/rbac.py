from __future__ import annotations

from enum import StrEnum

from app.models.user import RoleName


class PermissionKey(StrEnum):
    USERS_READ = "users:read"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DISABLE = "users:disable"
    ROLES_READ = "roles:read"
    ROLES_CREATE = "roles:create"
    ROLES_UPDATE = "roles:update"
    PERMISSIONS_READ = "permissions:read"
    INCIDENTS_READ = "incidents:read"
    INCIDENTS_CREATE = "incidents:create"
    INCIDENTS_UPDATE = "incidents:update"
    INCIDENTS_ASSIGN = "incidents:assign"
    INCIDENTS_CLOSE = "incidents:close"
    INCIDENTS_COMMENT = "incidents:comment"
    ALERTS_READ = "alerts:read"
    ALERTS_INGEST = "alerts:ingest"
    ALERTS_UPDATE = "alerts:update"
    ALERTS_WRITE = "alerts:write"
    KUBERNETES_READ = "kubernetes:read"
    KUBERNETES_WRITE = "kubernetes:write"
    METRICS_READ = "metrics:read"
    PROMETHEUS_READ = "prometheus:read"
    LOKI_READ = "loki:read"
    LOGS_READ = "logs:read"
    RCA_READ = "rca:read"
    RCA_CREATE = "rca:create"
    REMEDIATION_READ = "remediation:read"
    REMEDIATION_EXECUTE = "remediation:execute"
    REMEDIATION_APPROVE = "remediation:approve"
    REMEDIATION_CANCEL = "remediation:cancel"
    INTEGRATIONS_READ = "integrations:read"
    INTEGRATIONS_CREATE = "integrations:create"
    INTEGRATIONS_UPDATE = "integrations:update"
    INTEGRATIONS_DELETE = "integrations:delete"
    INTEGRATIONS_TEST = "integrations:test"
    INTEGRATIONS_SYNC = "integrations:sync"
    DASHBOARDS_READ = "dashboards:read"
    AUDIT_LOGS_READ = "audit_logs:read"
    AI_READ = "ai:read"
    AI_ANALYZE = "ai:analyze"
    JENKINS_READ = "jenkins:read"
    JENKINS_WRITE = "jenkins:write"
    JENKINS_ANALYZE = "jenkins:analyze"


ALL_PERMISSIONS = {permission.value for permission in PermissionKey}
READ_ONLY_PERMISSIONS = {
    PermissionKey.INCIDENTS_READ.value,
    PermissionKey.ALERTS_READ.value,
    PermissionKey.KUBERNETES_READ.value,
    PermissionKey.METRICS_READ.value,
    PermissionKey.LOGS_READ.value,
    PermissionKey.RCA_READ.value,
    PermissionKey.DASHBOARDS_READ.value,
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    RoleName.ADMIN.value: set(ALL_PERMISSIONS),
    RoleName.SRE.value: {
        PermissionKey.INCIDENTS_READ.value,
        PermissionKey.INCIDENTS_CREATE.value,
        PermissionKey.INCIDENTS_UPDATE.value,
        PermissionKey.INCIDENTS_ASSIGN.value,
        PermissionKey.INCIDENTS_CLOSE.value,
        PermissionKey.INCIDENTS_COMMENT.value,
        PermissionKey.ALERTS_READ.value,
        PermissionKey.ALERTS_INGEST.value,
        PermissionKey.ALERTS_UPDATE.value,
        PermissionKey.ALERTS_WRITE.value,
        PermissionKey.KUBERNETES_READ.value,
        PermissionKey.KUBERNETES_WRITE.value,
        PermissionKey.METRICS_READ.value,
        PermissionKey.PROMETHEUS_READ.value,
        PermissionKey.LOKI_READ.value,
        PermissionKey.LOGS_READ.value,
        PermissionKey.RCA_READ.value,
        PermissionKey.RCA_CREATE.value,
        PermissionKey.REMEDIATION_READ.value,
        PermissionKey.REMEDIATION_EXECUTE.value,
        PermissionKey.REMEDIATION_APPROVE.value,
        PermissionKey.REMEDIATION_CANCEL.value,
        PermissionKey.INTEGRATIONS_READ.value,
        PermissionKey.INTEGRATIONS_TEST.value,
        PermissionKey.INTEGRATIONS_SYNC.value,
        PermissionKey.DASHBOARDS_READ.value,
        PermissionKey.AUDIT_LOGS_READ.value,
        PermissionKey.AI_READ.value,
        PermissionKey.AI_ANALYZE.value,
        PermissionKey.JENKINS_READ.value,
        PermissionKey.JENKINS_WRITE.value,
        PermissionKey.JENKINS_ANALYZE.value,
    },
    RoleName.DEVELOPER.value: {
        PermissionKey.INCIDENTS_READ.value,
        PermissionKey.INCIDENTS_CREATE.value,
        PermissionKey.INCIDENTS_UPDATE.value,
        PermissionKey.INCIDENTS_COMMENT.value,
        PermissionKey.ALERTS_READ.value,
        PermissionKey.KUBERNETES_READ.value,
        PermissionKey.METRICS_READ.value,
        PermissionKey.PROMETHEUS_READ.value,
        PermissionKey.LOKI_READ.value,
        PermissionKey.LOGS_READ.value,
        PermissionKey.RCA_READ.value,
        PermissionKey.RCA_CREATE.value,
        PermissionKey.REMEDIATION_READ.value,
        PermissionKey.REMEDIATION_EXECUTE.value,
        PermissionKey.DASHBOARDS_READ.value,
        PermissionKey.AI_READ.value,
        PermissionKey.AI_ANALYZE.value,
        PermissionKey.JENKINS_READ.value,
        PermissionKey.JENKINS_WRITE.value,
        PermissionKey.JENKINS_ANALYZE.value,
    },
    RoleName.VIEWER.value: set(READ_ONLY_PERMISSIONS),
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    RoleName.ADMIN.value: "Full platform administration access.",
    RoleName.SRE.value: "Incident response, RCA, and approved remediation access.",
    RoleName.DEVELOPER.value: "Service collaboration and limited operational access.",
    RoleName.VIEWER.value: "Read-only operational visibility.",
}


def permissions_for_roles(role_names: list[str]) -> set[str]:
    permissions: set[str] = set()
    for role_name in role_names:
        permissions.update(ROLE_PERMISSIONS.get(role_name, set()))
    return permissions
