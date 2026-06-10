import uuid, secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from api.core.rbac import require_tenant, require_permission, Permission
from api.core.email import send_org_invitation_email
from db.session import SessionLocal
from db.models import OrganizationInvitation, Organization, OrganizationMember, User
import os

router = APIRouter(prefix="/members", tags=["Team Members"])

class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "Recruiter"

@router.get("", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def list_members(tenant_id: str = Depends(require_tenant)):
    db = SessionLocal()
    try:
        members = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == tenant_id
        ).all()
        result = []
        for m in members:
            user = db.query(User).filter(User.id == m.user_id).first()
            if user:
                result.append({
                    "id": m.id,
                    "email": user.email,
                    "role": m.role,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None
                })
        return result
    finally:
        db.close()

@router.post("/invite", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def invite_member(req: InviteRequest, tenant_id: str = Depends(require_tenant)):
    db = SessionLocal()
    try:
        org = db.query(Organization).filter(Organization.id == tenant_id).first()
        token = secrets.token_urlsafe(32)
        invite = OrganizationInvitation(
            id=str(uuid.uuid4()),
            organization_id=tenant_id,
            email=req.email,
            role=req.role,
            token=token,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(invite)
        db.commit()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        invite_link = f"{frontend_url}/accept-invite?token={token}"
        import asyncio
        asyncio.create_task(send_org_invitation_email(req.email, org.name if org else "your team", req.role, invite_link))
        return {"message": f"Invitation sent to {req.email}", "token": token}
    finally:
        db.close()

@router.delete("/{member_id}", dependencies=[Depends(require_permission(Permission.MANAGE_MEMBERS))])
async def remove_member(member_id: str, tenant_id: str = Depends(require_tenant)):
    db = SessionLocal()
    try:
        member = db.query(OrganizationMember).filter(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == tenant_id
        ).first()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        db.delete(member)
        db.commit()
        return {"message": "Member removed"}
    finally:
        db.close()
