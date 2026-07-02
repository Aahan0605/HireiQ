import os
import base64
import tempfile
import heapq
import logging
import json
import re
from celery import Celery
import sentry_sdk
from db import get_supabase
from api.core.encryption import encrypt_field

from api.core.encryption import encrypt_field


# Initialize Sentry for background workers
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    def scrub_sensitive_data(event, hint):
        if 'request' in event:
            req = event['request']
            req.pop('cookies', None)
            headers = req.get('headers', {})
            headers.pop('Authorization', None)
            headers.pop('authorization', None)
            headers.pop('Cookie', None)
            headers.pop('cookie', None)
            
            data = req.get('data')
            if data:
                if isinstance(data, dict):
                    for k in list(data.keys()):
                        if any(sensitive in k.lower() for sensitive in ('password', 'resume_text', 'raw_text', 'card', 'token', 'secret', 'content_b64')):
                            data[k] = '[scrubbed]'
                elif isinstance(data, str):
                    try:
                        parsed = json.loads(data)
                        if isinstance(parsed, dict):
                            for k in list(parsed.keys()):
                                if any(sensitive in k.lower() for sensitive in ('password', 'resume_text', 'raw_text', 'card', 'token', 'secret', 'content_b64')):
                                    parsed[k] = '[scrubbed]'
                            req['data'] = json.dumps(parsed)
                    except Exception:
                        pass
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        traces_sample_rate=0.2,
        profiles_sample_rate=0.2,
        send_default_pii=False,
        before_send=scrub_sensitive_data,
    )

# Initialize Celery App
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("hireiq_tasks", broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery for secure rediss:// brokers if needed
if REDIS_URL.startswith("rediss://"):
    import ssl
    celery_app.conf.update(
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE}
    )

# Configure Celery for secure rediss:// brokers if needed
if REDIS_URL.startswith("rediss://"):
    import ssl
    celery_app.conf.update(
        broker_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE},
        redis_backend_use_ssl={"ssl_cert_reqs": ssl.CERT_NONE}
    )

logger = logging.getLogger("celery_worker")
logging.basicConfig(level=logging.INFO)

@celery_app.task(name="tasks.process_resume", max_retries=3, default_retry_delay=10)
def process_resume_task(candidate_id: str, filename: str, content_b64: str, tenant_id: str):
    """Celery background task: Decodes resume file, extracts text, runs TF-IDF match, extracts insights, and updates Candidate record in Supabase."""
    logger.info("Starting background resume task for Candidate ID: %s, Tenant: %s", candidate_id, tenant_id)
    supabase = get_supabase()
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
            supabase.table("candidates").update({
                "pipeline_stage": "rejected",
                "raw_text": encrypt_field("Error: Could not extract text from document.")
            }).eq("id", candidate_id).execute()
            return

        # Load active jobs for this tenant
        res_jobs = supabase.table("jobs").select("*").eq("recruiter_id", tenant_id).execute()
        jobs_list = res_jobs.data
        
        import asyncio
        from engine.score_fusion import compute_full_candidate_score
        from parser.feature_extractor import extract_contact
        
        contact = extract_contact(text)
        github_username = contact.get("github")
        if github_username:
            github_username = github_username.split("github.com/")[-1].split("/")[0]
        
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
            role_type = "backend_engineer" if "backend" in str(best_job.get("title", "")).lower() else "frontend_engineer"
            req_skills = best_job.get("required_skills") or []
            if isinstance(req_skills, str):
                req_skills_list = [s.strip() for s in req_skills.split(",") if s.strip()]
            else:
                req_skills_list = req_skills
                
            jd_features = {
                "required_skills": req_skills_list,
                "preferred_skills": [],
                "min_experience": best_job.get("min_experience", 0),
                "max_experience": 99,
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
        
        final_score = int(scoring_res.get("final_score", 60))
        blind_score = final_score
        
        # Compute Blind Score using bias auditor
        if best_job:
            try:
                from engine.bias_auditor import compute_blind_score
                blind_res = asyncio.run(compute_blind_score(
                    candidate_name=candidate_name,
                    resume_text=text,
                    jd_features=jd_features,
                    role_type=role_type
                ))
                blind_score = int(blind_res.get("final_score", final_score))
            except Exception as e:
                logger.warning("Failed to compute blind score: %s", e)
                
        # Parse education tier
        edu = scoring_res.get("resume_features", {}).get("education_level", "other")
        edu_tier = "other"
        if edu.lower() in ("bachelors", "masters", "phd", "other"):
            edu_tier = edu.lower()

        # Update candidate database entity in Supabase
        insights = scoring_res.get("insights", {})
        if not isinstance(insights, dict):
            insights = {}
        insights["resume_base64"] = content_b64
        if contact.get("linkedin"):
            insights["linkedin"] = contact.get("linkedin")
        insights["completeness_score"] = insights.get("completeness_score") or 80
        insights["ats_score"] = insights.get("ats_score") or 75

        db_record = {
            "full_name": candidate_name,
            "email": contact.get("email") or f"{candidate_id[:8]}@example.com",
            "phone": contact.get("phone", ""),
            "location": contact.get("location") or "Remote",
            "experience_years": int(scoring_res.get("resume_features", {}).get("experience_years", 0)),
            "education_tier": edu_tier,
            "skills": scoring_res.get("resume_features", {}).get("skills", []),
            "raw_text": encrypt_field(text),
            "match_score": final_score,
            "completeness_score": insights.get("completeness_score", 80),
            "ats_score": insights.get("ats_score", 75),
            "career_tier": scoring_res.get("resume_features", {}).get("role", "Software Engineer"),
            "key_strengths": insights.get("ai_summary", {}).get("strengths", []),
            "development_gaps": insights.get("ai_summary", {}).get("gaps", []),
            "potential_concerns": insights.get("ai_summary", {}).get("concerns", []),
            "pipeline_stage": "screening" if final_score < 85 else "shortlisted",
            "github_url": github_username or "",
            "github_stars": scoring_res.get("external_signals", {}).get("github", {}).get("total_stars", 0),
            "github_languages": scoring_res.get("external_signals", {}).get("github", {}).get("languages", []),
            "github_commits_last_year": int(scoring_res.get("external_signals", {}).get("github", {}).get("commit_frequency_per_week", 0) * 52),
            "blind_score": blind_score,
            "resume_filename": filename,
            "interview_questions": [],
            "insights": {**insights, "evaluation_breakdown": scoring_res.get("evaluation_breakdown") or {}},
            "summary": insights.get("ai_summary", {}).get("executive_summary", ""),
            "experience": scoring_res.get("resume_features", {}).get("experience_timeline", [])
        }
        
        if best_job:
            db_record["job_id"] = best_job["id"]

        supabase.table("candidates").update(db_record).eq("id", candidate_id).execute()
        logger.info("Successfully processed Candidate ID: %s", candidate_id)

    except Exception as e:
        logger.error("Error running resume Celery worker task: %s", e)
        try:
            supabase.table("candidates").update({
                "pipeline_stage": "rejected",
                "raw_text": encrypt_field(f"Error during parsing: {str(e)}")
            }).eq("id", candidate_id).execute()
        except Exception:
            pass
        raise e
