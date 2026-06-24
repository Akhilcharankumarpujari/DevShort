from app.models.user import RoleName
from app.security.rbac import ALL_PERMISSIONS, PermissionKey, ROLE_PERMISSIONS, permissions_for_roles


def test_admin_has_all_permissions() -> None:
    assert ROLE_PERMISSIONS[RoleName.ADMIN.value] == ALL_PERMISSIONS


def test_viewer_is_read_only() -> None:
    viewer_permissions = ROLE_PERMISSIONS[RoleName.VIEWER.value]

    assert PermissionKey.INCIDENTS_READ.value in viewer_permissions
    assert PermissionKey.ALERTS_READ.value in viewer_permissions
    assert PermissionKey.REMEDIATION_EXECUTE.value not in viewer_permissions


def test_permissions_for_multiple_roles_are_combined() -> None:
    permissions = permissions_for_roles([RoleName.VIEWER.value, RoleName.DEVELOPER.value])

    assert PermissionKey.RCA_READ.value in permissions
    assert PermissionKey.INCIDENTS_CREATE.value in permissions
