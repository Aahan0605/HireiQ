from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import math
import heapq
from collections import Counter

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobCreate(BaseModel):
    title: str
    department: str
    location: str
    employment_type: str
    experience_required: int
    description: str
    required_skills: str  # comma-separated
    status: str           # Open / Closed / Draft


# In-memory store (seeded on startup)
jobs_db: list[dict] = []


def _seed():
    # Time Complexity: O(1) — runs once on startup
    if jobs_db:
        return
    jobs_db.extend([
        {
            "id": 1, "title": "Senior Frontend Engineer",
            "department": "Engineering", "location": "Remote",
            "employment_type": "Full-time", "experience_required": 3,
            "description": "We need a strong frontend engineer to build scalable UI components",
            "required_skills": "React,TypeScript,Next.js,CSS,Testing,Webpack",
            "status": "Open", "created_at": datetime.now().isoformat(),
        },
        {
            "id": 2, "title": "Backend Python Developer",
            "department": "Engineering", "location": "Bangalore",
            "employment_type": "Full-time", "experience_required": 2,
            "description": "Backend developer for our core API and data pipeline",
            "required_skills": "Python,FastAPI,PostgreSQL,Docker,Redis,CI/CD",
            "status": "Open", "created_at": datetime.now().isoformat(),
        },
        {
            "id": 3, "title": "ML Engineer",
            "department": "AI/ML", "location": "Remote",
            "employment_type": "Full-time", "experience_required": 2,
            "description": "ML engineer to build and deploy machine learning models",
            "required_skills": "Python,PyTorch,Scikit-learn,MLflow,Statistics,Spark",
            "status": "Open", "created_at": datetime.now().isoformat(),
        },
        {
            "id": 4, "title": "Fullstack Developer",
            "department": "Product", "location": "Hybrid",
            "employment_type": "Full-time", "experience_required": 2,
            "description": "Fullstack engineer to work across frontend and backend systems",
            "required_skills": "React,Node.js,PostgreSQL,Docker,TypeScript,REST APIs",
            "status": "Open", "created_at": datetime.now().isoformat(),
        },
    ])


_seed()


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
def get_jobs():
    # Time Complexity: O(1)
    return jobs_db


@router.post("", status_code=201)
def create_job(job: JobCreate):
    # Time Complexity: O(n) to find max id
    new_id = max((j["id"] for j in jobs_db), default=0) + 1
    record = {**job.model_dump(), "id": new_id, "created_at": datetime.now().isoformat()}
    jobs_db.append(record)
    return record


@router.get("/{job_id}")
def get_job(job_id: int):
    # Time Complexity: O(n)
    job = next((j for j in jobs_db if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.put("/{job_id}")
def update_job(job_id: int, job: JobCreate):
    # Time Complexity: O(n)
    idx = next((i for i, j in enumerate(jobs_db) if j["id"] == job_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Job not found")
    jobs_db[idx].update(job.model_dump())
    return jobs_db[idx]


@router.delete("/{job_id}")
def delete_job(job_id: int):
    # Time Complexity: O(n)
    global jobs_db
    before = len(jobs_db)
    jobs_db = [j for j in jobs_db if j["id"] != job_id]
    if len(jobs_db) == before:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "deleted"}


# ── MATCHING ──────────────────────────────────────────────────

@router.get("/{job_id}/matches")
def job_matches(job_id: int):
    """
    Rank all candidates for a job using TF-IDF cosine similarity + Max-Heap.
    Time Complexity: O(n log n) — TF-IDF scoring O(n*m) + Max-Heap ranking O(n log n)
    """
    from .candidates import candidates_db  # import here to avoid circular at module load

    job = next((j for j in jobs_db if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_text = job["description"] + " " + job["required_skills"].replace(",", " ")
    job_skills = {s.strip().lower() for s in job["required_skills"].split(",")}

    max_heap: list = []

    for c in candidates_db:
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
