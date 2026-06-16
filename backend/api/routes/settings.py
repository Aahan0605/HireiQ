from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from api.core.rbac import require_tenant
from db import get_supabase

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(require_tenant)]
)

class Weights(BaseModel):
    resume: float = 0.4
    github: float = 0.3
    leetcode: float = 0.2
    portfolio: float = 0.1

class Thresholds(BaseModel):
    strong: int = 85
    match: int = 60
    weak: int = 40

# ── Shared in-memory store ─────────────────────────────────────
# Other routes import `active_weights` to apply user-configured weights.
active_weights: dict[str, float] = {
    "resume":    0.4,
    "github":    0.3,
    "leetcode":  0.2,
    "portfolio": 0.1,
}

active_thresholds: dict[str, int] = {
    "strong": 85,
    "match":  60,
    "weak":   40,
}

@router.post("/weights")
def update_weights(weights: Weights):
    global active_weights
    active_weights = weights.model_dump()
    return {"status": "saved", "weights": active_weights}

@router.post("/thresholds")
def update_thresholds(thresholds: Thresholds):
    global active_thresholds
    active_thresholds = thresholds.model_dump()
    return {"status": "saved", "thresholds": active_thresholds}

@router.get("/weights")
def get_weights():
    return active_weights

@router.get("/thresholds")
def get_thresholds():
    return active_thresholds

@router.get("/analytics")
async def get_analytics(tenant_id: str = Depends(require_tenant)):
    """Return analytics summary from database."""
    try:
        supabase = get_supabase()
        
        # Fetch recruiter plan info
        rec_res = supabase.table("recruiters").select("plan").eq("id", tenant_id).execute()
        plan_name = rec_res.data[0].get("plan", "free") if rec_res.data else "free"
        
        # Fetch all candidates for tenant
        res = supabase.table("candidates").select("match_score, skills, created_at, pipeline_stage, education_tier").eq("recruiter_id", tenant_id).execute()
        candidates = res.data or []
        
        total = len(candidates)
        strong = sum(1 for c in candidates if (c.get("match_score") or 0.0) >= 85)
        match = sum(1 for c in candidates if 60 <= (c.get("match_score") or 0.0) < 85)
        weak = sum(1 for c in candidates if (c.get("match_score") or 0.0) < 60)
        avg_score = sum((c.get("match_score") or 0.0) for c in candidates) / total if total > 0 else 0.0
        
        # Recent uploads count (7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = 0
        for c in candidates:
            created_str = c.get("created_at")
            if created_str:
                try:
                    clean_dt = created_str.split("+")[0].split("Z")[0]
                    created_dt = datetime.fromisoformat(clean_dt)
                    if created_dt >= seven_days_ago:
                        recent += 1
                except Exception:
                    pass
                     
        # Top skills aggregation
        skill_freq = {}
        for c in candidates:
            skills = c.get("skills") or []
            for s in skills:
                s_clean = s.strip()
                if s_clean:
                    skill_freq[s_clean] = skill_freq.get(s_clean, 0) + 1
        top_skills = sorted(skill_freq.items(), key=lambda x: -x[1])[:10]

        # Pipeline stage, education tier, and score distribution aggregations
        pipeline_stages_freq = {
            "screening": 0,
            "shortlisted": 0,
            "interviewing": 0,
            "offer": 0,
            "hired": 0,
            "rejected": 0
        }
        education_freq = {
            "bachelors": 0,
            "masters": 0,
            "phd": 0,
            "other": 0
        }
        score_dist = {
            "0-49": 0,
            "50-69": 0,
            "70-84": 0,
            "85-100": 0
        }

        for c in candidates:
            stage = c.get("pipeline_stage") or "screening"
            if stage in pipeline_stages_freq:
                pipeline_stages_freq[stage] += 1
            else:
                pipeline_stages_freq["screening"] += 1

            edu = c.get("education_tier") or "other"
            if edu in education_freq:
                education_freq[edu] += 1
            else:
                education_freq["other"] += 1

            score = c.get("match_score") or 0.0
            if score < 50:
                score_dist["0-49"] += 1
            elif score < 70:
                score_dist["50-69"] += 1
            elif score < 85:
                score_dist["70-84"] += 1
            else:
                score_dist["85-100"] += 1
        
        return {
            "total_candidates": total,
            "strong_matches": strong,
            "matches": match,
            "weak_matches": weak,
            "average_score": round(avg_score, 1),
            "recent_uploads_7d": recent,
            "top_skills": [{"skill": s, "count": count} for s, count in top_skills],
            "pipeline_stages": [{"stage": k.capitalize(), "count": v} for k, v in pipeline_stages_freq.items()],
            "education_breakdown": [{"tier": k.capitalize(), "count": v} for k, v in education_freq.items()],
            "score_distribution": [{"range": k, "count": v} for k, v in score_dist.items()],
            "storage_backend": "supabase",
            "plan_name": plan_name.upper(),
            "sub_status": "active"
        }
    except Exception as e:
        return {
            "total_candidates": 0,
            "strong_matches": 0,
            "matches": 0,
            "weak_matches": 0,
            "average_score": 0.0,
            "recent_uploads_7d": 0,
            "top_skills": [],
            "pipeline_stages": [{"stage": k.capitalize(), "count": 0} for k in ["screening","shortlisted","interviewing","offer","hired","rejected"]],
            "education_breakdown": [{"tier": k.capitalize(), "count": 0} for k in ["bachelors","masters","phd","other"]],
            "score_distribution": [{"range": k, "count": 0} for k in ["0-49","50-69","70-84","85-100"]],
            "storage_backend": "supabase",
            "plan_name": "FREE",
            "sub_status": "active"
        }

@router.get("/worker-status")
def get_worker_status():
    """Check if the Redis broker and Celery worker are online."""
    import socket
    from urllib.parse import urlparse
    from tasks.worker import celery_app, REDIS_URL
    
    # Quick socket check to prevent blocking if Redis is offline
    try:
        parsed = urlparse(REDIS_URL)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=0.1):
            redis_up = True
    except Exception:
        redis_up = False

    if not redis_up:
        return {"status": "fallback", "message": "Redis broker offline. Using local background tasks fallback."}

    try:
        ping_result = celery_app.control.ping(timeout=0.3)
        if ping_result:
            return {"status": "online", "message": f"Active worker(s) detected: {list(ping_result[0].keys()) if ping_result else ''}"}
        else:
            return {"status": "fallback", "message": "Redis online, worker process offline. Using local background tasks fallback."}
    except Exception:
        return {"status": "fallback", "message": "Redis broker offline. Using local background tasks fallback."}

@router.get("/db-status")
def get_db_status():
    """Return database connection status."""
    return {
        "supabase_available": True,
        "supabase_url": "Supabase Managed Cloud",
        "sqlite_path": "Deprecated",
        "sqlite_size_mb": 0.0,
    }

class UpdatePlanRequest(BaseModel):
    plan_name: str

@router.post("/billing/update-plan")
def update_plan(req: UpdatePlanRequest, tenant_id: str = Depends(require_tenant)):
    """Manually update the plan for testing/mock purposes."""
    plan_lower = req.plan_name.lower()
    if plan_lower not in ("free", "pro", "enterprise"):
        raise HTTPException(status_code=400, detail="Invalid plan name")
        
    supabase = get_supabase()
    res = supabase.table("recruiters").update({"plan": plan_lower}).eq("id", tenant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Recruiter record not found")
        
    return {"status": "success", "plan_name": plan_lower}
