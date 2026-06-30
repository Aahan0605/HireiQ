from fastapi import HTTPException, status
from db import get_supabase

PLAN_QUOTAS = {
    "free": {"parses": 999999, "jobs": 999999, "seats": 999999},
    "pro": {"parses": 999999, "jobs": 999999, "seats": 999999},
    "enterprise": {"parses": 999999, "jobs": 999999, "seats": 999999}
}

def get_recruiter(recruiter_id: str) -> dict:
    supabase = get_supabase()
    res = supabase.table("recruiters").select("*").eq("id", recruiter_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    return res.data[0]

def check_cv_upload_limit(db, tenant_id: str):
    recruiter = get_recruiter(tenant_id)
    plan = recruiter.get("plan", "free").lower()
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    used = recruiter.get("cv_upload_count", 0)
    if used >= quotas["parses"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"CV parsing quota exhausted ({used}/{quotas['parses']}). Please upgrade your plan in Settings."
        )

def check_job_creation_limit(db, tenant_id: str):
    recruiter = get_recruiter(tenant_id)
    plan = recruiter.get("plan", "free").lower()
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    
    # Count jobs
    supabase = get_supabase()
    res = supabase.table("jobs").select("id", count="exact").eq("recruiter_id", tenant_id).execute()
    used = res.count if res.count is not None else len(res.data)
    if used >= quotas["jobs"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Job posting quota exhausted ({used}/{quotas['jobs']}). Please upgrade your plan in Settings."
        )

def increment_cv_parses(db, tenant_id: str):
    supabase = get_supabase()
    recruiter = get_recruiter(tenant_id)
    current_count = recruiter.get("cv_upload_count", 0)
    supabase.table("recruiters").update({"cv_upload_count": current_count + 1}).eq("id", tenant_id).execute()

def increment_jobs_created(db, tenant_id: str):
    # In the new schema, jobs count is checked dynamically.
    # We don't have a jobs_created_used column in recruiters. We can just pass.
    pass

def check_seat_limit(db, tenant_id: str):
    recruiter = get_recruiter(tenant_id)
    company = recruiter.get("company")
    plan = recruiter.get("plan", "free").lower()
    quotas = PLAN_QUOTAS.get(plan, PLAN_QUOTAS["free"])
    if not company:
        return
    supabase = get_supabase()
    res = supabase.table("recruiters").select("id", count="exact").eq("company", company).execute()
    used = res.count if res.count is not None else len(res.data)
    if used >= quotas["seats"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Team seat limit reached ({used}/{quotas['seats']}). Please upgrade your plan in Settings."
        )
