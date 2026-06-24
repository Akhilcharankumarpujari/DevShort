from __future__ import annotations

from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.user import Permission, RefreshToken, Role, RoleName, User, UserStatus
from app.schemas.auth import AuthResponse, TokenPair, UserResponse
from app.security.password import hash_password, verify_password
from app.security.rbac import ALL_PERMISSIONS, ROLE_DESCRIPTIONS, ROLE_PERMISSIONS, permissions_for_roles
from app.security.tokens import TokenService, hash_refresh_token


class AuthService:
    def __init__(self, session: AsyncSession, token_service: TokenService | None = None) -> None:
        self.session = session
        self.token_service = token_service or TokenService()

    async def register_user(self, *, email: str, full_name: str, password: str) -> AuthResponse:
        await self.ensure_default_roles_and_permissions()
        existing = await self.get_user_by_email(email)
        if existing is not None:
            raise AppException(
                status_code=409,
                code="email_already_registered",
                message="A user with this email already exists.",
            )

        user_count = await self.session.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None)))
        role_name = RoleName.ADMIN.value if user_count == 0 else RoleName.VIEWER.value
        role = await self.get_role_by_name(role_name)
        if role is None:
            raise AppException(
                status_code=500,
                code="default_role_missing",
                message="Default role could not be initialized.",
            )

        user = User(
            email=email.lower(),
            full_name=full_name.strip(),
            hashed_password=hash_password(password),
            status=UserStatus.ACTIVE.value,
            roles=[role],
        )
        self.session.add(user)
        await self.session.commit()
        registered_user = await self.get_user_by_id(user.id)
        if registered_user is None:
            raise AppException(status_code=500, code="registration_failed", message="Registration failed.")
        return await self.build_auth_response(registered_user)

    async def login(self, *, email: str, password: str) -> AuthResponse:
        user = await self.get_user_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AppException(
                status_code=401,
                code="invalid_credentials",
                message="Email or password is incorrect.",
            )
        if not user.is_active:
            raise AppException(
                status_code=403,
                code="user_disabled",
                message="User account is disabled.",
            )

        user.last_login_at = datetime.now(UTC)
        await self.session.commit()
        user = await self.get_user_by_id(user.id)
        if user is None:
            raise AppException(status_code=500, code="login_failed", message="Login failed.")
        return await self.build_auth_response(user)

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self.token_service.decode_token(refresh_token, expected_type="refresh")
        user_id = UUID(str(payload["sub"]))
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if stored_token is None or stored_token.user_id != user_id:
            raise AppException(status_code=401, code="invalid_refresh_token", message="Refresh token is invalid.")
        if stored_token.revoked_at is not None or stored_token.expires_at <= datetime.now(UTC):
            raise AppException(status_code=401, code="refresh_token_expired", message="Refresh token is expired or revoked.")

        user = await self.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise AppException(status_code=401, code="invalid_refresh_token", message="Refresh token is invalid.")

        access_token, expires_in = self.create_access_token_for_user(user)
        new_refresh_token, _, expires_at = self.token_service.create_refresh_token(subject=str(user.id))
        new_refresh_model = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=expires_at,
        )
        self.session.add(new_refresh_model)
        await self.session.flush()

        stored_token.revoked_at = datetime.now(UTC)
        stored_token.replaced_by_token_id = new_refresh_model.id
        await self.session.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    async def logout(self, refresh_token: str) -> None:
        self.token_service.decode_token(refresh_token, expected_type="refresh")
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if stored_token is not None and stored_token.revoked_at is None:
            stored_token.revoked_at = datetime.now(UTC)
            await self.session.commit()

    async def ensure_default_roles_and_permissions(self) -> None:
        permissions_by_key: dict[str, Permission] = {}
        existing_permissions = await self.session.scalars(select(Permission))
        for permission in existing_permissions:
            permissions_by_key[permission.key] = permission

        for permission_key in sorted(ALL_PERMISSIONS):
            existing_permission = permissions_by_key.get(permission_key)
            if existing_permission is None:
                new_permission = Permission(key=permission_key, description=f"Allows {permission_key}.")
                self.session.add(new_permission)
                permissions_by_key[permission_key] = new_permission

        await self.session.flush()

        existing_roles = await self.session.scalars(select(Role).options(selectinload(Role.permissions)))
        roles_by_name = {role.name: role for role in existing_roles}
        for role_name, permission_keys in ROLE_PERMISSIONS.items():
            role = roles_by_name.get(role_name)
            if role is None:
                role = Role(
                    name=role_name,
                    description=ROLE_DESCRIPTIONS.get(role_name),
                    is_system=True,
                )
                self.session.add(role)
                roles_by_name[role_name] = role
            role.permissions = [permissions_by_key[key] for key in sorted(permission_keys)]

        await self.session.commit()

    async def get_user_by_email(self, email: str) -> User | None:
        return cast(
            User | None,
            await self.session.scalar(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.email == email.lower(), User.deleted_at.is_(None))
            ),
        )

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return cast(
            User | None,
            await self.session.scalar(
                select(User)
                .options(selectinload(User.roles).selectinload(Role.permissions))
                .where(User.id == user_id, User.deleted_at.is_(None))
            ),
        )

    async def get_role_by_name(self, name: str) -> Role | None:
        return cast(
            Role | None,
            await self.session.scalar(
                select(Role).options(selectinload(Role.permissions)).where(Role.name == name)
            ),
        )

    async def build_auth_response(self, user: User) -> AuthResponse:
        tokens = await self.issue_tokens(user)
        return AuthResponse(user=user_to_response(user), tokens=tokens)

    async def issue_tokens(self, user: User) -> TokenPair:
        access_token, expires_in = self.create_access_token_for_user(user)
        refresh_token, _, expires_at = self.token_service.create_refresh_token(subject=str(user.id))
        self.session.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token),
                expires_at=expires_at,
            )
        )
        await self.session.commit()
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    def create_access_token_for_user(self, user: User) -> tuple[str, int]:
        roles = [role.name for role in user.roles]
        permissions = sorted(permissions_for_roles(roles))
        return self.token_service.create_access_token(
            subject=str(user.id),
            roles=roles,
            permissions=permissions,
        )


def user_to_response(user: User) -> UserResponse:
    roles = list(user.roles)
    permissions = sorted(permissions_for_roles([role.name for role in roles]))
    return UserResponse.model_validate(user).model_copy(update={"permissions": permissions})

