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

router = APIRouter(prefix="/members", tags=["Team Members"], dependencies=[Depends(require_tenant)])

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
        raise HTTPException(status_code=500, detail=f"Failed to fetch team members: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Failed to send invitation: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")
