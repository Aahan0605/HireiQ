import json
import logging
import uuid
import datetime
import os
from pathlib import Path
from typing import Any
from sqlalchemy import desc
from db.session import SessionLocal, engine
from db.models import User, Candidate, Job, AuditLog, OrganizationMember, Subscription
from db.crypto import encrypt_field, decrypt_field
from api.core.rbac import get_tenant_id

logger = logging.getLogger(__name__)

# Auto-migrate tables on start for local dev fallback (Alembic runs in prod)
try:
    from db.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas bootstrapped successfully.")
except Exception as e:
    logger.error("Failed to auto-migrate database tables: %s", e)

# ─── Helper Deserializers ──────────────────────────────────────

def _json_loads(v: str | None) -> Any:
    if not v:
        return []
    try:
        return json.loads(v)
    except Exception:
        return []

def _json_dumps(v: Any) -> str:
    if v is None:
        return "[]"
    return json.dumps(v)

def _candidate_to_dict(c: Candidate) -> dict:
    """Serialize Candidate SQLAlchemy object to dict, decrypting PII fields."""
    name = decrypt_field(c.name)
    email = decrypt_field(c.email)
    resume_text = decrypt_field(c.resume_text)
    
    skills = _json_loads(c.skills)
    experience = _json_loads(c.experience)
    job_matches = _json_loads(c.job_matches)
    radar_data = _json_loads(c.radar_data)
    qa = _json_loads(c.qa)
    insights = _json_loads(c.insights)
    
    return {
        "id": c.id,
        "organization_id": c.organization_id,
        "name": name,
        "email": email,
        "role": c.role,
        "github": c.github,
        "linkedin": c.linkedin,
        "location": c.location,
        "score": c.score,
        "blind_score": c.blind_score,
        "status": c.status,
        "summary": c.summary,
        "resume_text": resume_text or "",
        "skills": skills,
        "experience": experience,
        "job_matches": job_matches,
        "jobMatches": job_matches,  # frontend camelCase compatibility
        "radar_data": radar_data,
        "radarData": radar_data,    # frontend camelCase compatibility
        "qa": qa,
        "insights": insights,
        "analyzed_at": c.analyzed_at.isoformat() if c.analyzed_at else None
    }

def _job_to_dict(j: Job) -> dict:
    """Serialize Job SQLAlchemy object to dict."""
    return {
        "id": j.id,
        "organization_id": j.organization_id,
        "title": j.title,
        "company": j.company,
        "department": j.department,
        "employment_type": j.employment_type,
        "location": j.location,
        "description": j.description,
        "required_skills": j.required_skills,
        "preferred_skills": j.preferred_skills,
        "experience_required": j.experience_required,
        "max_experience": j.max_experience,
        "salary_range": j.salary_range,
        "status": j.status,
        "created_at": j.created_at.isoformat() if j.created_at else None
    }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — candidates (Scope-Isolated by tenant_id)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def save_candidate(candidate: dict) -> dict:
    """Upsert a candidate model, encrypting PII fields."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    if not tenant_id:
        tenant_id = candidate.get("organization_id", "default-tenant")

    try:
        cand_id = candidate.get("id")
        existing = db.query(Candidate).filter(Candidate.id == cand_id).first()
        
        # Encrypt name, email, and resume_text fields
        enc_name = encrypt_field(candidate.get("name"))
        enc_email = encrypt_field(candidate.get("email"))
        if "resume_text" in candidate:
            enc_resume = encrypt_field(candidate.get("resume_text"))
        else:
            enc_resume = existing.resume_text if existing else None

        if existing:
            existing.organization_id = tenant_id
            existing.name = enc_name
            existing.email = enc_email
            existing.role = candidate.get("role", existing.role)
            existing.github = candidate.get("github", existing.github)
            existing.linkedin = candidate.get("linkedin", existing.linkedin)
            existing.location = candidate.get("location", existing.location)
            existing.score = candidate.get("score", existing.score)
            existing.blind_score = candidate.get("blind_score", existing.blind_score)
            existing.status = candidate.get("status", existing.status)
            existing.summary = candidate.get("summary", existing.summary)
            existing.resume_text = enc_resume
            existing.skills = _json_dumps(candidate.get("skills", _json_loads(existing.skills)))
            existing.experience = _json_dumps(candidate.get("experience", _json_loads(existing.experience)))
            existing.job_matches = _json_dumps(candidate.get("jobMatches", candidate.get("job_matches", _json_loads(existing.job_matches))))
            existing.radar_data = _json_dumps(candidate.get("radarData", candidate.get("radar_data", _json_loads(existing.radar_data))))
            existing.qa = _json_dumps(candidate.get("qa", _json_loads(existing.qa)))
            existing.insights = _json_dumps(candidate.get("insights", _json_loads(existing.insights)))
        else:
            new_cand = Candidate(
                id=cand_id or str(uuid.uuid4()),
                organization_id=tenant_id,
                name=enc_name,
                email=enc_email,
                role=candidate.get("role", "Software Engineer"),
                github=candidate.get("github", ""),
                linkedin=candidate.get("linkedin", ""),
                location=candidate.get("location", "Remote"),
                score=candidate.get("score", 0),
                blind_score=candidate.get("blind_score", candidate.get("score", 0)),
                status=candidate.get("status", "Analyzing"),
                summary=candidate.get("summary", ""),
                resume_text=enc_resume if enc_resume is not None else "",
                skills=_json_dumps(candidate.get("skills", [])),
                experience=_json_dumps(candidate.get("experience", [])),
                job_matches=_json_dumps(candidate.get("jobMatches", candidate.get("job_matches", []))),
                radar_data=_json_dumps(candidate.get("radarData", candidate.get("radar_data", []))),
                qa=_json_dumps(candidate.get("qa", [])),
                insights=_json_dumps(candidate.get("insights", {}))
            )
            db.add(new_cand)
            
        db.commit()
        return candidate
    except Exception as e:
        db.rollback()
        logger.error("Failed to save candidate: %s", e)
        raise e
    finally:
        db.close()

async def fetch_all_candidates() -> list[dict]:
    """Fetch all candidates belonging to active tenant context, ordered by score descending."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Candidate)
        if tenant_id:
            query = query.filter(Candidate.organization_id == tenant_id)
        results = query.order_by(desc(Candidate.score)).all()
        return [_candidate_to_dict(c) for c in results]
    finally:
        db.close()

async def fetch_candidate_by_id(candidate_id: str) -> dict | None:
    """Fetch a candidate by ID, scoped to active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Candidate).filter(Candidate.id == candidate_id)
        if tenant_id:
            query = query.filter(Candidate.organization_id == tenant_id)
        c = query.first()
        return _candidate_to_dict(c) if c else None
    finally:
        db.close()

async def delete_candidate(candidate_id: str) -> bool:
    """Delete candidate from active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Candidate).filter(Candidate.id == candidate_id)
        if tenant_id:
            query = query.filter(Candidate.organization_id == tenant_id)
        candidate = query.first()
        if candidate:
            db.delete(candidate)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete candidate: %s", e)
        return False
    finally:
        db.close()

async def get_candidate_count() -> int:
    """Count candidates belonging to active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Candidate)
        if tenant_id:
            query = query.filter(Candidate.organization_id == tenant_id)
        return query.count()
    finally:
        db.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — jobs (Scope-Isolated by tenant_id)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def save_job(job: dict) -> dict:
    """Upsert job entity scoped to tenant."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    if not tenant_id:
        tenant_id = job.get("organization_id", "default-tenant")

    try:
        job_id = str(job.get("id"))
        existing = db.query(Job).filter(Job.id == job_id).first()
        if existing:
            existing.organization_id = tenant_id
            existing.title = job.get("title", existing.title)
            existing.company = job.get("company", existing.company)
            existing.department = job.get("department", existing.department)
            existing.employment_type = job.get("employment_type", existing.employment_type)
            existing.location = job.get("location", existing.location)
            existing.description = job.get("description", existing.description)
            existing.required_skills = job.get("required_skills", existing.required_skills)
            existing.preferred_skills = job.get("preferred_skills", existing.preferred_skills)
            existing.experience_required = job.get("experience_required", existing.experience_required)
            existing.max_experience = job.get("max_experience", existing.max_experience)
            existing.salary_range = job.get("salary_range", existing.salary_range)
            existing.status = job.get("status", existing.status)
        else:
            new_job = Job(
                id=job_id,
                organization_id=tenant_id,
                title=job.get("title"),
                company=job.get("company", "HireIQ Corp"),
                department=job.get("department", "Engineering"),
                employment_type=job.get("employment_type", "Full-time"),
                location=job.get("location"),
                description=job.get("description"),
                required_skills=job.get("required_skills"),
                preferred_skills=job.get("preferred_skills", ""),
                experience_required=job.get("experience_required", 0),
                max_experience=job.get("max_experience", 99),
                salary_range=job.get("salary_range", ""),
                status=job.get("status", "Open")
            )
            db.add(new_job)
        db.commit()
        return job
    except Exception as e:
        db.rollback()
        logger.error("Failed to save job: %s", e)
        raise e
    finally:
        db.close()

async def fetch_all_jobs() -> list[dict]:
    """Fetch all jobs scoped to active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Job)
        if tenant_id:
            query = query.filter(Job.organization_id == tenant_id)
        results = query.order_by(desc(Job.created_at)).all()
        return [_job_to_dict(j) for j in results]
    finally:
        db.close()

async def fetch_job_by_id(job_id: str) -> dict | None:
    """Fetch job by ID within active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Job).filter(Job.id == job_id)
        if tenant_id:
            query = query.filter(Job.organization_id == tenant_id)
        j = query.first()
        return _job_to_dict(j) if j else None
    finally:
        db.close()

async def delete_job(job_id: str) -> bool:
    """Delete a job by ID scoped to active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        query = db.query(Job).filter(Job.id == job_id)
        if tenant_id:
            query = query.filter(Job.organization_id == tenant_id)
        job = query.first()
        if job:
            db.delete(job)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error("Failed to delete job: %s", e)
        return False
    finally:
        db.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — users
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def save_user(user: dict) -> dict:
    """Create or update user account."""
    db = SessionLocal()
    try:
        user_id = user.get("id")
        existing = db.query(User).filter(User.id == user_id).first()
        if existing:
            existing.email = user.get("email", existing.email)
            existing.hashed_password = user.get("hashed_password", existing.hashed_password)
            existing.role = user.get("role", existing.role)
        else:
            new_user = User(
                id=user_id,
                email=user.get("email"),
                hashed_password=user.get("hashed_password"),
                role=user.get("role", "Recruiter")
            )
            db.add(new_user)
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        logger.error("Failed to save user: %s", e)
        raise e
    finally:
        db.close()

async def fetch_user_by_email(email: str) -> dict | None:
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if not u:
            return None
        return {"id": u.id, "email": u.email, "hashed_password": u.hashed_password, "role": u.role}
    finally:
        db.close()

async def fetch_user_by_id(user_id: str) -> dict | None:
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.id == user_id).first()
        if not u:
            return None
        return {"id": u.id, "email": u.email, "hashed_password": u.hashed_password, "role": u.role}
    finally:
        db.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — analytics & status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def log_analytics_event(event_type: str, payload: dict):
    db = SessionLocal()
    tenant_id = get_tenant_id() or "system"
    try:
        event = AuditLog(
            organization_id=tenant_id,
            action=event_type,
            ip_address=payload.get("ip_address", "127.0.0.1")
        )
        db.add(event)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Failed to log audit event: %s", e)
    finally:
        db.close()

async def get_analytics_summary() -> dict:
    """Summarize stats for active tenant context."""
    db = SessionLocal()
    tenant_id = get_tenant_id()
    try:
        from db.models import Subscription
        plan_name = "Free"
        sub_status = "active"
        if tenant_id:
            sub = db.query(Subscription).filter(Subscription.organization_id == tenant_id).first()
            if sub:
                plan_name = sub.plan_name
                sub_status = sub.status

        query = db.query(Candidate)
        if tenant_id:
            query = query.filter(Candidate.organization_id == tenant_id)
        
        candidates = query.all()
        total = len(candidates)
        strong = sum(1 for c in candidates if c.score >= 85)
        match = sum(1 for c in candidates if 60 <= c.score < 85)
        weak = sum(1 for c in candidates if c.score < 60)
        avg_score = sum(c.score for c in candidates) / total if total > 0 else 0
        
        # Recent uploads count
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        recent = sum(1 for c in candidates if c.analyzed_at and c.analyzed_at >= seven_days_ago)
        
        # Top skills aggregation
        skill_freq = {}
        for c in candidates:
            for s in _json_loads(c.skills):
                skill_freq[s] = skill_freq.get(s, 0) + 1
        top_skills = sorted(skill_freq.items(), key=lambda x: -x[1])[:10]
        
        # Fetch DB stats info
        db_path = Path(__file__).resolve().parent / "hireiq.db"
        sqlite_size = round(db_path.stat().st_size / 1024 / 1024, 2) if db_path.exists() else 0

        return {
            "total_candidates": total,
            "strong_matches": strong,
            "matches": match,
            "weak_matches": weak,
            "average_score": round(avg_score, 1),
            "recent_uploads_7d": recent,
            "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
            "storage_backend": "postgresql" if "postgresql" in engine.url.drivername else "sqlite",
            "sqlite_size_mb": sqlite_size,
            "plan_name": plan_name,
            "sub_status": sub_status
        }
    finally:
        db.close()

def get_db_status() -> dict:
    """Settings dashboard health parameters."""
    db_path = Path(__file__).resolve().parent / "hireiq.db"
    sqlite_size = round(db_path.stat().st_size / 1024 / 1024, 2) if db_path.exists() else 0
    return {
        "supabase_available": "postgresql" in engine.url.drivername,
        "supabase_url": str(engine.url.host) if engine.url.host else "",
        "sqlite_path": str(db_path),
        "sqlite_size_mb": sqlite_size,
    }
