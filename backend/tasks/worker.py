import os
import base64
import tempfile
import heapq
import logging
import json
import re
from celery import Celery
from db.session import SessionLocal
from db.models import Candidate, Job
from db.crypto import encrypt_field
import sentry_sdk

# Initialize Sentry for background workers
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0
    )

# Initialize Celery App
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("hireiq_tasks", broker=REDIS_URL, backend=REDIS_URL)

# Basic Celery logging setup
logger = logging.getLogger("celery_worker")
logging.basicConfig(level=logging.INFO)

@celery_app.task(name="tasks.process_resume", max_retries=3, default_retry_delay=10)
def process_resume_task(candidate_id: str, filename: str, content_b64: str, tenant_id: str):
    """Celery background task: Decodes resume file, extracts text, runs TF-IDF match, extracts insights, and updates Candidate record."""
    logger.info("Starting background resume task for Candidate ID: %s, Tenant: %s", candidate_id, tenant_id)
    db = SessionLocal()
    try:
        content = base64.b64decode(content_b64)
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        text = ""

        # Create temporary file to pass to parser
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if ext == ".pdf":
                from parser.resume_parser import extract_text_from_file
                text = extract_text_from_file(tmp_path)
            else:
                text = content.decode("utf-8", errors="replace")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        if not text or not text.strip():
            logger.warning("Extraction returned empty text for candidate: %s", candidate_id)
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                candidate.status = "Extraction Failed"
                candidate.summary = "Error: Could not extract text from document."
                db.commit()
            return

        # Load active jobs for this tenant
        jobs_list = db.query(Job).filter(Job.organization_id == tenant_id).all()
        
        # Determine candidate's details using compute_full_candidate_score against the first/best job
        import asyncio
        from engine.score_fusion import compute_full_candidate_score
        from parser.feature_extractor import extract_contact
        
        contact = extract_contact(text)
        github_username = contact.get("github")
        if github_username:
            github_username = github_username.split("github.com/")[-1].split("/")[0]
        linkedin_url = contact.get("linkedin")
        
        best_job = jobs_list[0] if jobs_list else None
        role_type = "backend_engineer"
        jd_features = {
            "required_skills": [],
            "preferred_skills": [],
            "min_experience": 0,
            "max_experience": 99,
            "education_required": "unknown"
        }
        
        if best_job:
            role_type = "backend_engineer" if "backend" in best_job.title.lower() else "frontend_engineer"
            jd_features = {
                "required_skills": [s.strip() for s in best_job.required_skills.split(",") if s.strip()] if best_job.required_skills else [],
                "preferred_skills": [s.strip() for s in best_job.preferred_skills.split(",") if s.strip()] if best_job.preferred_skills else [],
                "min_experience": best_job.experience_required,
                "max_experience": best_job.max_experience,
                "education_required": "unknown"
            }
            
        candidate_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        
        # Run scoring engine asynchronously using asyncio.run
        scoring_res = asyncio.run(compute_full_candidate_score(
            candidate_name=candidate_name,
            resume_text=text,
            jd_features=jd_features,
            github_username=github_username,
            role_type=role_type
        ))
        
        final_score = int(scoring_res["final_score"])
        blind_score = final_score
        
        # Compute Blind Score using bias auditor
        if best_job:
            try:
                from engine.bias_auditor import compute_blind_score
                blind_res = compute_blind_score(
                    candidate_name=candidate_name,
                    resume_text=text,
                    jd_features=jd_features,
                    role_type=role_type
                )
                blind_score = int(blind_res.get("final_score", final_score))
            except Exception as e:
                logger.warning("Failed to compute blind score: %s", e)
                
        # Build job_matches list for all jobs
        job_matches = []
        for job in jobs_list:
            from engine.matcher import compute_match_breakdown
            job_jd = {
                "required_skills": [s.strip() for s in job.required_skills.split(",") if s.strip()] if job.required_skills else [],
                "preferred_skills": [s.strip() for s in job.preferred_skills.split(",") if s.strip()] if job.preferred_skills else [],
                "min_experience": job.experience_required,
                "max_experience": job.max_experience,
                "education_required": "unknown"
            }
            match_breakdown = compute_match_breakdown(
                resume_features=scoring_res["resume_features"],
                jd_features=job_jd,
                github_signals=scoring_res["external_signals"]["github"],
                linkedin_signals=scoring_res["external_signals"]["linkedin"]
            )
            job_matches.append({
                "job_id": job.id,
                "job_title": job.title,
                "tfidf_score": match_breakdown["overall_match_percentage"],
                "matched_skills": scoring_res["matched_skills"],
                "missing_skills": scoring_res["missing_skills"],
            })

        # Update candidate database entity
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            candidate.name = encrypt_field(candidate_name)
            candidate.email = encrypt_field(contact.get("email") or f"{candidate_id[:8]}@example.com")
            candidate.role = scoring_res["resume_features"].get("role", "Software Engineer")
            candidate.github = github_username or ""
            candidate.linkedin = linkedin_url or ""
            candidate.score = final_score
            candidate.blind_score = blind_score
            candidate.status = "Strong Match" if final_score > 85 else "Match"
            candidate.summary = scoring_res["insights"]["ai_summary"]["executive_summary"]
            candidate.resume_text = text
            candidate.skills = json.dumps(scoring_res["resume_features"].get("skills", []))
            candidate.experience = json.dumps([{"title": "Experience", "company": "Various", "duration": f"{scoring_res['resume_features'].get('experience_years', 0.0)} years"}])
            candidate.job_matches = json.dumps(job_matches)
            candidate.radar_data = json.dumps([])
            candidate.insights = json.dumps(scoring_res["insights"])
            db.commit()
            logger.info("Successfully processed Candidate ID: %s", candidate_id)

    except Exception as e:
        logger.error("Error running resume Celery worker task: %s", e)
        db.rollback()
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if candidate:
            candidate.status = "Failed"
            candidate.summary = f"Error during parsing: {str(e)}"
            db.commit()
        raise e
    finally:
        db.close()
