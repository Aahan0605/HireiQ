import uuid
import secrets
import os
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from api.core.rbac import require_tenant, require_permission, Permission
from api.core.email import send_org_invitation_email
from db import get_supabase
from api.core.error_handling import safe_error_response

router = APIRouter(prefix="/members", tags=["Team Members"])

class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "Recruiter"

@router.get("", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def list_members(tenant_id: str = Depends(require_tenant)):
    supabase = get_supabase()
    try:
        # 1. Fetch current recruiter's company
        rec_res = supabase.table("recruiters").select("company").eq("id", tenant_id).execute()
        company = rec_res.data[0].get("company") if rec_res.data else None
        if not company:
            return []
            
        # 2. Fetch all recruiters with matching company name
        members_res = supabase.table("recruiters").select("id, email, role, created_at").eq("company", company).execute()
        
        return [{
            "id": m["id"],
            "email": m["email"],
            "role": m.get("role", "Recruiter"),
            "joined_at": m.get("created_at")
        } for m in members_res.data]
    except Exception as e:
        raise safe_error_response(e, "Failed to fetch team members.")

@router.post("/invite", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def invite_member(req: InviteRequest, tenant_id: str = Depends(require_tenant)):
    supabase = get_supabase()
    try:
        # 1. Fetch current recruiter's company
        rec_res = supabase.table("recruiters").select("company").eq("id", tenant_id).execute()
        company = rec_res.data[0].get("company") if rec_res.data else None
        if not company:
            raise HTTPException(status_code=400, detail="Please set your company name in Settings before inviting team members.")

        # 2. Check seats limit
        from api.core.limits import check_seat_limit
        check_seat_limit(None, tenant_id)

        # 3. Insert organization invitation
        token = secrets.token_urlsafe(32)
        supabase.table("organization_invitations").insert({
            "id": str(uuid.uuid4()),
            "company": company,
            "email": req.email,
            "role": req.role,
            "token": token,
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }).execute()
        
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        invite_link = f"{frontend_url}/accept-invite?token={token}"
        
        asyncio.create_task(send_org_invitation_email(req.email, company, req.role, invite_link))
        return {"message": f"Invitation sent to {req.email}", "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Failed to send invitation.")

@router.delete("/{member_id}", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def remove_member(member_id: str, tenant_id: str = Depends(require_tenant)):
    supabase = get_supabase()
    try:
        # 1. Fetch current recruiter's company
        rec_res = supabase.table("recruiters").select("company").eq("id", tenant_id).execute()
        company = rec_res.data[0].get("company") if rec_res.data else None
        if not company:
            raise HTTPException(status_code=403, detail="Not authorized")

        # 2. Check if target member exists in same company
        member_res = supabase.table("recruiters").select("company").eq("id", member_id).execute()
        if not member_res.data or member_res.data[0].get("company") != company:
            raise HTTPException(status_code=404, detail="Member not found in your team")
            
        if member_id == tenant_id:
            raise HTTPException(status_code=400, detail="You cannot remove yourself from the team")

        # 3. Remove from company
        supabase.table("recruiters").update({"company": None}).eq("id", member_id).execute()
        return {"message": "Member removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Failed to remove member.")

from pydantic import BaseModel as PydanticBaseModel

class AcceptInviteRequest(PydanticBaseModel):
    token: str
    password: str  # required only if the invited email has no existing account

@router.get("/invite/{token}", dependencies=[])
async def get_invite_details(token: str):
    """Public endpoint — lets the accept-invite page show who/what org invited them before login."""
    supabase = get_supabase()
    res = supabase.table("organization_invitations").select("*").eq("token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Invitation not found or already used.")
    invite = res.data[0]

    expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00")) if isinstance(invite["expires_at"], str) else invite["expires_at"]
    if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo) if expires_at.tzinfo else expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This invitation has expired.")

    existing_user = supabase.table("recruiters").select("id").eq("email", invite["email"]).execute()

    return {
        "email": invite["email"],
        "role": invite["role"],
        "company": invite["company"],
        "account_exists": bool(existing_user.data),
    }

@router.post("/invite/{token}/accept", dependencies=[])
async def accept_invite(token: str, req: AcceptInviteRequest):
    """Public endpoint — redeems an invite token. Creates a new recruiter account 
    if one doesn't exist for that email, or attaches the existing account to the company."""
    supabase = get_supabase()
    res = supabase.table("organization_invitations").select("*").eq("token", token).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Invitation not found or already used.")
    invite = res.data[0]

    expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00")) if isinstance(invite["expires_at"], str) else invite["expires_at"]
    now = datetime.utcnow().replace(tzinfo=expires_at.tzinfo) if expires_at.tzinfo else datetime.utcnow()
    if expires_at < now:
        raise HTTPException(status_code=400, detail="This invitation has expired.")

    existing = supabase.table("recruiters").select("*").eq("email", invite["email"]).execute()

    from api.core.security import get_password_hash, create_access_token

    if existing.data:
        # Existing account — just attach to the company and update role
        user = existing.data[0]
        supabase.table("recruiters").update({
            "company": invite["company"],
            "role": invite["role"],
        }).eq("id", user["id"]).execute()
        user_id = user["id"]
    else:
        # New account — require a password to create one
        if not req.password or len(req.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters to create your account.")
        new_id = str(uuid.uuid4())
        supabase.table("recruiters").insert({
            "id": new_id,
            "email": invite["email"],
            "hashed_password": get_password_hash(req.password),
            "role": invite["role"],
            "company": invite["company"],
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        user_id = new_id

    # Delete the invitation so it can't be reused
    supabase.table("organization_invitations").delete().eq("token", token).execute()

    access_token = create_access_token(subject=user_id)
    return {
        "message": "Invitation accepted. Welcome to the team!",
        "access_token": access_token,
        "user": {"id": user_id, "email": invite["email"], "role": invite["role"]},
    }
