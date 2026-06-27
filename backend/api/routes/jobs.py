from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import math
import heapq
import uuid
import logging
from collections import Counter
from api.core.dependencies import get_current_user
from api.core.rbac import require_tenant, require_permission, Permission
from api.core.limits import check_job_creation_limit, increment_jobs_created
from db import get_supabase
from api.core.encryption import decrypt_field

from api.core.encryption import decrypt_field


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    dependencies=[Depends(require_tenant)]
)

class JobCreate(BaseModel):
    title: str
    department: str = "Engineering"
    location: str = "Remote"
    employment_type: str = "Full-time"
    experience_required: int = 0
    description: str
    required_skills: str  # comma-separated
    status: str = "Open"

def _job_to_dict(j: dict) -> dict:
    if not j:
        return {}
    # Convert required_skills array to comma-separated string if it is a list
    req_skills = j.get("required_skills")
    if isinstance(req_skills, list):
        j["required_skills"] = ",".join(req_skills)
    # Map recruiter_id to organization_id for frontend backward compatibility
    j["organization_id"] = j.get("recruiter_id")
    # Set defaults for fields not in new jobs table
    j.setdefault("company", "HireIQ Corp")
    j.setdefault("department", "Engineering")
    j.setdefault("employment_type", "Full-time")
    j.setdefault("location", "Remote")
    j.setdefault("experience_required", j.get("min_experience", 0))
    j.setdefault("salary_range", "")
    j.setdefault("status", "Open")
    return j

async def fetch_all_jobs(recruiter_id: str) -> list[dict]:
    supabase = get_supabase()
    res = supabase.table("jobs").select("*").eq("recruiter_id", recruiter_id).execute()
    return [_job_to_dict(j) for j in res.data]

async def fetch_job_by_id(job_id: str, recruiter_id: str) -> dict | None:
    supabase = get_supabase()
    res = supabase.table("jobs").select("*").eq("id", job_id).eq("recruiter_id", recruiter_id).execute()
    return _job_to_dict(res.data[0]) if res.data else None

async def save_job(job: dict, recruiter_id: str) -> dict:
    supabase = get_supabase()
    req_skills = job.get("required_skills", "")
    if isinstance(req_skills, str):
        req_skills_list = [s.strip() for s in req_skills.split(",") if s.strip()]
    else:
        req_skills_list = req_skills
        
    db_record = {
        "title": job.get("title"),
        "description": job.get("description"),
        "required_skills": req_skills_list,
        "min_experience": job.get("experience_required", 0),
        "recruiter_id": recruiter_id
    }
    
    is_update = False
    if "id" in job and job["id"] and not str(job["id"]).startswith("seed-"):
        exists_res = supabase.table("jobs").select("id").eq("id", job["id"]).eq("recruiter_id", recruiter_id).execute()
        if exists_res.data:
            is_update = True

    if is_update:
        # update
        res = supabase.table("jobs").update(db_record).eq("id", job["id"]).eq("recruiter_id", recruiter_id).execute()
    else:
        # insert
        if "id" in job and not str(job["id"]).startswith("seed-"):
            db_record["id"] = job["id"]
        res = supabase.table("jobs").insert(db_record).execute()
        
    return _job_to_dict(res.data[0]) if res.data else {}

async def delete_job_db(job_id: str, recruiter_id: str):
    supabase = get_supabase()
    supabase.table("jobs").delete().eq("id", job_id).eq("recruiter_id", recruiter_id).execute()

async def _seed_if_empty(recruiter_id: str):
    existing = await fetch_all_jobs(recruiter_id)
    if existing:
        return
    seed_jobs = [
        {
            "title": "Senior Frontend Engineer",
            "experience_required": 3,
            "description": "We need a strong frontend engineer to build scalable UI components",
            "required_skills": "React,TypeScript,Next.js,CSS,Testing,Webpack",
        },
        {
            "title": "Backend Python Developer",
            "experience_required": 2,
            "description": "Backend developer for our core API and data pipeline",
            "required_skills": "Python,FastAPI,PostgreSQL,Docker,Redis,CI/CD",
        },
        {
            "title": "ML Engineer",
            "experience_required": 2,
            "description": "ML engineer to build and deploy machine learning models",
            "required_skills": "Python,PyTorch,Scikit-learn,MLflow,Statistics,Spark",
        },
        {
            "title": "Fullstack Developer",
            "experience_required": 2,
            "description": "Fullstack engineer to work across frontend and backend systems",
            "required_skills": "React,Node.js,PostgreSQL,Docker,TypeScript,REST APIs",
        },
    ]
    for job in seed_jobs:
        await save_job(job, recruiter_id)

def _cosine_similarity(text_a: str, text_b: str) -> float:
    tokens_a = text_a.lower().split()
    tokens_b = text_b.lower().split()
    if not tokens_a or not tokens_b:
        return 0.0

    freq_a = Counter(tokens_a)
    freq_b = Counter(tokens_b)

    vocab = set(freq_a) | set(freq_b)
    dot = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in vocab)
    mag_a = math.sqrt(sum(v * v for v in freq_a.values()))
    mag_b = math.sqrt(sum(v * v for v in freq_b.values()))

    return dot / (mag_a * mag_b) if (mag_a * mag_b) else 0.0

# ── CRUD ──────────────────────────────────────────────────────

@router.get("")
async def get_jobs(tenant_id: str = Depends(require_tenant)):
    try:
        await _seed_if_empty(tenant_id)
        return await fetch_all_jobs(tenant_id)
    except Exception as e:
        logger.error(f"Error in GET /jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs. Please try again.")

@router.post("", status_code=201, dependencies=[Depends(require_permission(Permission.CREATE_JOB))])
async def create_job(job: JobCreate, tenant_id: str = Depends(require_tenant)):
    try:
        check_job_creation_limit(None, tenant_id)
        record = {
            **job.model_dump(),
            "id": str(uuid.uuid4()),
            "company": "HireIQ Corp"
        }
        res = await save_job(record, tenant_id)
        increment_jobs_created(None, tenant_id)
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in POST /jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to create job. Please try again.")

@router.get("/{job_id}")
async def get_job(job_id: str, tenant_id: str = Depends(require_tenant)):
    try:
        job = await fetch_job_by_id(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /jobs/{job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job. Please try again.")

@router.put("/{job_id}", dependencies=[Depends(require_permission(Permission.CREATE_JOB))])
async def update_job(job_id: str, job: JobCreate, tenant_id: str = Depends(require_tenant)):
    try:
        existing = await fetch_job_by_id(job_id, tenant_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")
        record = {
            **job.model_dump(),
            "id": job_id,
            "company": existing.get("company", "HireIQ Corp")
        }
        return await save_job(record, tenant_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PUT /jobs/{job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update job. Please try again.")

@router.delete("/{job_id}", dependencies=[Depends(require_permission(Permission.CREATE_JOB))])
async def delete_job(job_id: str, tenant_id: str = Depends(require_tenant)):
    try:
        existing = await fetch_job_by_id(job_id, tenant_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Job not found")
        await delete_job_db(job_id, tenant_id)
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in DELETE /jobs/{job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job. Please try again.")

# ── MATCHING ──────────────────────────────────────────────────

@router.get("/{job_id}/matches")
async def job_matches(job_id: str, tenant_id: str = Depends(require_tenant)):
    try:
        job = await fetch_job_by_id(job_id, tenant_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job_text = job["description"] + " " + job["required_skills"].replace(",", " ")
        job_skills = {s.strip().lower() for s in job["required_skills"].split(",")}

        supabase = get_supabase()
        res = supabase.table("candidates").select("*").eq("recruiter_id", tenant_id).execute()
        candidates_list = res.data

        max_heap = []

        for c in candidates_list:
            cand_skills_list = c.get("skills", [])
            cand_text = " ".join(cand_skills_list) + " " + decrypt_field(c.get("raw_text") or "")
            cand_skills = {s.lower() for s in cand_skills_list}

            sim = _cosine_similarity(job_text, cand_text)
            score = min(100, int(sim * 100))

            matched = sorted(job_skills & cand_skills)
            missing = sorted(job_skills - cand_skills)

            item = {
                "id": c["id"],
                "name": c.get("full_name") or c.get("name") or "Unnamed Candidate",
                "role": c.get("career_tier", "Software Engineer"),
                "match_score": score,
                "matched_skills": matched,
                "missing_skills": missing,
            }
            heapq.heappush(max_heap, (-score, c["id"], item))

        ranked = []
        while max_heap:
            ranked.append(heapq.heappop(max_heap)[2])

        return ranked
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GET /jobs/{job_id}/matches: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute job matches.")
