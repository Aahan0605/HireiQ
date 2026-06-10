import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from db.models import Subscription

# Quota configurations for SaaS tiers
PLAN_QUOTAS = {
    "Free": {"parses": 5, "jobs": 1, "seats": 1},
    "Pro": {"parses": 50, "jobs": 10, "seats": 3},
    "Business": {"parses": 500, "jobs": 100, "seats": 15},
    "Enterprise": {"parses": 999999, "jobs": 999999, "seats": 999999}
}

def get_or_create_subscription(db: Session, tenant_id: str) -> Subscription:
    """Retrieve organization's subscription record or initialize a Free one."""
    sub = db.query(Subscription).filter(Subscription.organization_id == tenant_id).first()
    if not sub:
        sub = Subscription(
            id=str(uuid.uuid4()),
            organization_id=tenant_id,
            plan_name="Free",
            status="active",
            cv_parses_used=0,
            jobs_created_used=0,
            team_seats_used=1
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub

def check_cv_upload_limit(db: Session, tenant_id: str):
    """Enforce resume parser limits based on active subscription plan."""
    sub = get_or_create_subscription(db, tenant_id)
    quotas = PLAN_QUOTAS.get(sub.plan_name, PLAN_QUOTAS["Free"])
    if sub.cv_parses_used >= quotas["parses"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"CV parsing quota exhausted ({sub.cv_parses_used}/{quotas['parses']}). Please upgrade your plan in Settings."
        )

def check_job_creation_limit(db: Session, tenant_id: str):
    """Enforce active job listing posting limits."""
    sub = get_or_create_subscription(db, tenant_id)
    quotas = PLAN_QUOTAS.get(sub.plan_name, PLAN_QUOTAS["Free"])
    if sub.jobs_created_used >= quotas["jobs"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Job posting quota exhausted ({sub.jobs_created_used}/{quotas['jobs']}). Please upgrade your plan in Settings."
        )

def increment_cv_parses(db: Session, tenant_id: str):
    """Increment candidate parsing usage counter."""
    sub = get_or_create_subscription(db, tenant_id)
    sub.cv_parses_used += 1
    db.commit()

def increment_jobs_created(db: Session, tenant_id: str):
    """Increment job posting usage counter."""
    sub = get_or_create_subscription(db, tenant_id)
    sub.jobs_created_used += 1
    db.commit()


def check_seat_limit(db: Session, tenant_id: str):
    """Enforce active team seats limits."""
    sub = get_or_create_subscription(db, tenant_id)
    quotas = PLAN_QUOTAS.get(sub.plan_name, PLAN_QUOTAS["Free"])
    if sub.team_seats_used >= quotas["seats"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Team seat limit reached ({sub.team_seats_used}/{quotas['seats']}). Please upgrade your plan in Settings."
        )
