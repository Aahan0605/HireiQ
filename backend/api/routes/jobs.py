from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import math
import heapq
import uuid
from collections import Counter
from db.supabase_client import save_job, fetch_all_jobs, fetch_job_by_id, delete_job as delete_job_db
from api.core.dependencies import get_current_user

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    dependencies=[Depends(get_current_user)]
)


class JobCreate(BaseModel):
    title: str
    department: str
    location: str
    employment_type: str
    experience_required: int
    description: str
    required_skills: str  # comma-separated
    status: str           # Open / Closed / Draft


async def _seed_if_empty():
    """Seeds default jobs into the database if empty."""
    existing = await fetch_all_jobs()
    if existing:
        return
    seed_jobs = [
        {
            "id": "1",
            "title": "Senior Frontend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 3,
            "description": "We need a strong frontend engineer to build scalable UI components",
            "required_skills": "React,TypeScript,Next.js,CSS,Testing,Webpack",
            "status": "Open",
        },
        {
            "id": "2",
            "title": "Backend Python Developer",
            "department": "Engineering",
            "location": "Bangalore",
            "employment_type": "Full-time",
            "experience_required": 2,
            "description": "Backend developer for our core API and data pipeline",
            "required_skills": "Python,FastAPI,PostgreSQL,Docker,Redis,CI/CD",
            "status": "Open",
        },
        {
            "id": "3",
            "title": "ML Engineer",
            "department": "AI/ML",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 2,
            "description": "ML engineer to build and deploy machine learning models",
            "required_skills": "Python,PyTorch,Scikit-learn,MLflow,Statistics,Spark",
            "status": "Open",
        },
        {
            "id": "4",
            "title": "Fullstack Developer",
            "department": "Product",
            "location": "Hybrid",
            "employment_type": "Full-time",
            "experience_required": 2,
            "description": "Fullstack engineer to work across frontend and backend systems",
            "required_skills": "React,Node.js,PostgreSQL,Docker,TypeScript,REST APIs",
            "status": "Open",
        },
    ]
    for job in seed_jobs:
        await save_job(job)


def _cosine_similarity(text_a: str, text_b: str) -> float:
    """
    Compute TF-IDF cosine similarity between two text strings.
    Time Complexity: O(n + m) where n, m are token counts.
    """
    tokens_a = text_a.lower().split()
    tokens_b = text_b.lower().split()
    if not tokens_a or not tokens_b:
        return 0.0

    # Term frequency vectors
    freq_a = Counter(tokens_a)
    freq_b = Counter(tokens_b)

    # Dot product over shared vocabulary
    vocab = set(freq_a) | set(freq_b)
    dot = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in vocab)
    mag_a = math.sqrt(sum(v * v for v in freq_a.values()))
    mag_b = math.sqrt(sum(v * v for v in freq_b.values()))

    return dot / (mag_a * mag_b) if (mag_a * mag_b) else 0.0


# ── CRUD ──────────────────────────────────────────────────────

@router.get("")
async def get_jobs():
    await _seed_if_empty()
    return await fetch_all_jobs()


@router.post("", status_code=201)
async def create_job(job: JobCreate):
    record = {
        **job.model_dump(),
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "company": "HireIQ Corp"
    }
    return await save_job(record)


@router.get("/{job_id}")
async def get_job(job_id: str):
    job = await fetch_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}")
async def update_job(job_id: str, job: JobCreate):
    existing = await fetch_job_by_id(job_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Job not found")
    record = {
        **job.model_dump(),
        "id": job_id,
        "company": existing.get("company", "HireIQ Corp")
    }
    return await save_job(record)


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    existing = await fetch_job_by_id(job_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Job not found")
    await delete_job_db(job_id)
    return {"status": "deleted"}


# ── MATCHING ──────────────────────────────────────────────────

@router.get("/{job_id}/matches")
async def job_matches(job_id: str):
    """
    Rank all candidates for a job using TF-IDF cosine similarity + Max-Heap.
    Time Complexity: O(n log n) — TF-IDF scoring O(n*m) + Max-Heap ranking O(n log n)
    """
    from db.supabase_client import fetch_all_candidates

    job = await fetch_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_text = job["description"] + " " + job["required_skills"].replace(",", " ")
    job_skills = {s.strip().lower() for s in job["required_skills"].split(",")}

    candidates_list = await fetch_all_candidates()
    max_heap: list = []

    for c in candidates_list:
        # Build candidate text from skills + summary
        cand_skills_list = c.get("skills", [])
        cand_text = " ".join(cand_skills_list) + " " + c.get("summary", "")
        cand_skills = {s.lower() for s in cand_skills_list}

        # TF-IDF cosine similarity score (0–100)
        sim = _cosine_similarity(job_text, cand_text)
        score = min(100, int(sim * 100))

        matched = sorted(job_skills & cand_skills)
        missing = sorted(job_skills - cand_skills)

        item = {
            "id": c["id"],
            "name": c["name"],
            "role": c.get("role", ""),
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing,
        }
        # Push negative score for max-heap behaviour using heapq (min-heap)
        heapq.heappush(max_heap, (-score, c["id"], item))

    # Pop all to get descending order
    ranked = []
    while max_heap:
        ranked.append(heapq.heappop(max_heap)[2])

    return ranked
