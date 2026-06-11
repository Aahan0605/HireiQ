import contextvars
from enum import Enum
from fastapi import Depends, HTTPException, status, Header
from api.core.dependencies import get_current_user
from db import get_supabase

# Thread-local / Async-safe context variables
tenant_context = contextvars.ContextVar("tenant_id", default=None)
user_role_context = contextvars.ContextVar("user_role", default=None)

class Permission(str, Enum):
    MANAGE_BILLING = "manage_billing"
    MANAGE_MEMBERS = "manage_members"
    CREATE_JOB = "create_job"
    DELETE_CANDIDATE = "delete_candidate"
    UPLOAD_RESUME = "upload_resume"
    VIEW_ANALYTICS = "view_analytics"

ROLE_PERMISSIONS = {
    "Super Admin": set(Permission),
    "Owner": {Permission.MANAGE_BILLING, Permission.MANAGE_MEMBERS, Permission.CREATE_JOB, Permission.DELETE_CANDIDATE, Permission.UPLOAD_RESUME, Permission.VIEW_ANALYTICS},
    "Admin": {Permission.MANAGE_MEMBERS, Permission.CREATE_JOB, Permission.DELETE_CANDIDATE, Permission.UPLOAD_RESUME, Permission.VIEW_ANALYTICS},
    "Recruiter": {Permission.CREATE_JOB, Permission.UPLOAD_RESUME, Permission.VIEW_ANALYTICS},
    "Hiring Manager": {Permission.UPLOAD_RESUME},
    "Viewer": set()
}

def get_tenant_id() -> str | None:
    """Get active tenant ID (recruiter ID) from request context."""
    return tenant_context.get()

async def require_tenant(
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency that extracts and validates the tenant ID.
    Scopes the request to a specific recruiter (the active tenant).
    """
    active_tenant = current_user["id"]
    tenant_context.set(active_tenant)
    user_role_context.set(current_user.get("role", "Owner"))
    return active_tenant

def require_permission(required_perm: Permission):
    """Factory dependency for enforcing RBAC permissions."""
    async def _has_permission(
        tenant_id: str = Depends(require_tenant)
    ):
        role = user_role_context.get()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned in this organization context."
            )
        
        perms = ROLE_PERMISSIONS.get(role, set())
        if role != "Super Admin" and required_perm not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permission: {required_perm.value}"
            )
        return True
    return _has_permission
