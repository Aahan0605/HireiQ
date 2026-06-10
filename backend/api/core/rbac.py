import contextvars
from enum import Enum
from fastapi import Depends, HTTPException, status, Header
from api.core.dependencies import get_current_user
from db.session import SessionLocal
from db.models import OrganizationMember, Organization

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
    """Get active tenant ID from request context."""
    return tenant_context.get()

async def require_tenant(
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    current_user: dict = Depends(get_current_user)
) -> str:
    """
    FastAPI dependency that extracts and validates the tenant ID.
    Scopes the request to a specific organization.
    """
    db = SessionLocal()
    try:
        # If tenant header is not specified, try to find default user workspace
        active_tenant = x_tenant_id
        if not active_tenant:
            member = db.query(OrganizationMember).filter(OrganizationMember.user_id == current_user["id"]).first()
            if member:
                active_tenant = member.organization_id
        
        if not active_tenant:
            # Create a default personal organization if they don't belong to one
            # to make onboarding frictionless
            import uuid
            org_id = str(uuid.uuid4())
            new_org = Organization(id=org_id, name="Personal Workspace", billing_tier="Free")
            new_member = OrganizationMember(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                user_id=current_user["id"],
                role="Owner"
            )
            # Create default subscription
            from db.models import Subscription
            new_sub = Subscription(
                id=str(uuid.uuid4()),
                organization_id=org_id,
                plan_name="Free",
                status="active",
                cv_parses_used=0,
                jobs_created_used=0
            )
            db.add(new_org)
            db.add(new_member)
            db.add(new_sub)
            db.commit()
            active_tenant = org_id

        # Verify user is member of organization
        member = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == active_tenant,
            OrganizationMember.user_id == current_user["id"]
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this organization."
            )

        # Set thread-local context variables
        tenant_context.set(active_tenant)
        user_role_context.set(member.role)
        return active_tenant
    finally:
        db.close()

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
