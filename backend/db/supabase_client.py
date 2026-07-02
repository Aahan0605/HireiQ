import os
import re
import uuid
import logging
from datetime import datetime
from functools import lru_cache
from supabase import create_client, Client
from api.core.encryption import encrypt_field, decrypt_field

from api.core.encryption import encrypt_field, decrypt_field


logger = logging.getLogger(__name__)

_checked_first_run = False

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    if not url:
        raise KeyError("SUPABASE_URL environment variable is missing.")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not key:
        raise KeyError("Neither SUPABASE_SERVICE_KEY nor SUPABASE_KEY is set in environment.")
    client = create_client(url, key)
    
    global _checked_first_run
    if not _checked_first_run:
        _checked_first_run = True
        try:
            res = client.table("recruiters").select("id").limit(1).execute()
            if not res.data:
                logger.warning("No users found. POST /auth/register to create the first account.")
                print("No users found. POST /auth/register to create the first account.")
        except Exception as e:
            logger.error(f"Error checking for existing recruiter accounts: {e}")
            
    return client

# ─── Candidate Mappers ───

def _candidate_to_dict(c: dict) -> dict:
    """Serialize Supabase candidate dict to frontend format."""
    if not c:
        return {}
        
    status_map = {
        "screening": "Screening",
        "shortlisted": "Shortlisted",
        "interviewing": "Interviewing",
        "offer": "Offer",
        "hired": "Hired",
        "rejected": "Rejected"
    }
    stage_val = c.get("stage") or c.get("pipeline_stage") or "screening"
    status = status_map.get(stage_val.lower(), "Screening")
    
    # If the candidate has the placeholder summary, return status: "Analyzing"
    summary_text = c.get("summary") or ""
    if "Analyzing resume, please wait..." in summary_text:
        status = "Analyzing"
    
    # If the candidate has the placeholder summary, return status: "Analyzing"
    summary_text = c.get("summary") or ""
    if "Analyzing resume, please wait..." in summary_text:
        status = "Analyzing"
    
    # Check if job title is pre-fetched/joined
    job_title = "Software Engineer"
    if "jobs" in c and c["jobs"]:
        if isinstance(c["jobs"], dict):
            job_title = c["jobs"].get("title", job_title)
        elif isinstance(c["jobs"], list) and c["jobs"]:
            job_title = c["jobs"][0].get("title", job_title)
            
    job_matches = []
    if c.get("job_id"):
        job_matches.append({
            "job_id": str(c["job_id"]),
            "job_title": job_title,
            "tfidf_score": c.get("match_score", 0.0),
            "matched_skills": c.get("skills") or [],
            "missing_skills": []
        })
        
    radar_data = [
        {"subject": "Commit Freq", "A": min(100, (c.get("github_commits_last_year") or 0) // 5), "fullMark": 100},
        {"subject": "Polyglot", "A": min(100, len(c.get("github_languages") or []) * 15), "fullMark": 100},
        {"subject": "Stars", "A": min(100, (c.get("github_stars") or 0) * 10), "fullMark": 100},
        {"subject": "Experience", "A": min(100, (c.get("experience_years") or 0) * 10), "fullMark": 100},
        {"subject": "ATS Score", "A": round(c.get("ats_score", 0.0) or c.get("match_score", 0.0)), "fullMark": 100}
    ]
    
    experience = []
    db_exp = c.get("experience")
    if db_exp:
        if isinstance(db_exp, list):
            experience = db_exp
        elif isinstance(db_exp, str):
            try:
                import json
                experience = json.loads(db_exp)
            except Exception:
                pass

    if not experience:
        raw_text = decrypt_field(c.get("raw_text") or "")
        if raw_text:
            try:
                from parser.feature_extractor import extract_experience
                extracted_exp = extract_experience(raw_text)
                for e in extracted_exp:
                    experience.append({
                        "title": e.get("title") or "Software Engineer",
                        "company": e.get("company") or "Various",
                        "date": e.get("date") or e.get("duration") or "Various Dates",
                        "description": e.get("description", "")
                    })
            except Exception as e:
                logger.warning(f"Failed to extract experience: {e}")

    if not experience:
        experience = [
            {"title": c.get("career_tier") or "Software Engineer", "company": "Previous Company", "date": f"{c.get('experience_years', 0)} Years"}
        ]
    
    raw_insights = c.get("insights") or {}
    if isinstance(raw_insights, str):
        try:
            import json
            raw_insights = json.loads(raw_insights)
        except Exception:
            raw_insights = {}
    elif not isinstance(raw_insights, dict):
        raw_insights = {}
    import copy
    db_insights = copy.deepcopy(raw_insights)
    has_resume = bool(db_insights.get("resume_base64"))
    
    github_val = c.get("github_url") or ""
    raw_linkedin = db_insights.get("linkedin") or db_insights.get("linkedin_details") or ""
    if isinstance(raw_linkedin, dict):
        linkedin_val = raw_linkedin.get("linkedin_url") or ""
    else:
        linkedin_val = str(raw_linkedin)
    if not github_val or not linkedin_val:
        raw_text = decrypt_field(c.get("raw_text") or "")
        if raw_text:
            try:
                from parser.feature_extractor import extract_contact
                contact = extract_contact(raw_text)
                if not github_val and contact.get("github"):
                    import re
                    gh = contact.get("github").strip()
                    gh = re.sub(r"^(?:https?:/?/?)?(?:www\.)?github\.com/", "", gh, flags=re.IGNORECASE)
                    gh = re.sub(r"^(?:https?:/?/?)?", "", gh, flags=re.IGNORECASE)
                    github_val = gh.strip("/").replace(" ", "").replace("\t", "")
                if not linkedin_val and contact.get("linkedin"):
                    linkedin_val = contact.get("linkedin").strip()
            except Exception as e:
                logger.warning(f"Failed to extract contact details from fallback: {e}")
        
    score = float(c.get("match_score") or 0.0)
    
    summary = c.get("summary")
    if not summary or "Analyzing resume" in summary or "please wait" in summary:
        name = c.get("full_name") or "The candidate"
        role = c.get("career_tier") or "Software Engineer"
        strengths = c.get("key_strengths") or []
        gaps = c.get("development_gaps") or []
        
        parts = [f"{name} is a {role} candidate with a match score of {round(score)}%."]
        if strengths:
            parts.append(f"Key strengths include {strengths[0].lower().rstrip('.')}.")
        if gaps:
            parts.append(f"Areas for attention: {gaps[0].lower().rstrip('.')}.")
        parts.append("Recommended for further technical assessment.")
        summary = " ".join(parts)
        
    # Generate fallbacks for nested objects if they are missing
    if "ai_summary" not in db_insights:
        db_insights["ai_summary"] = {
            "executive_summary": summary,
            "career_tier": c.get("career_tier") or "Software Engineer",
            "strengths": c.get("key_strengths") or [],
            "concerns": c.get("potential_concerns") or [],
            "interview_focus": [
                f"Assess proficiency in key strengths: {', '.join((c.get('key_strengths') or [])[:3])}" if c.get("key_strengths") else "Assess core software engineering practices.",
                f"Address potential concerns: {', '.join((c.get('potential_concerns') or [])[:2])}" if c.get("potential_concerns") else "Discuss past roles and career objectives."
            ],
            "verdict": "Strong Hire" if score >= 85 else ("Hire" if score >= 70 else ("Lean Hire" if score >= 55 else "No Hire"))
        }
        
    if "match_breakdown" not in db_insights:
        db_insights["match_breakdown"] = {
            "overall_match_percentage": round(score),
            "skills_match": round(max(0.0, min(100.0, score + 5.0))),
            "experience_match": min(100, max(40, (c.get("experience_years") or 0) * 10 + 30)),
            "education_match": 90 if c.get("education_tier") == "phd" else (85 if c.get("education_tier") == "masters" else (75 if c.get("education_tier") == "bachelors" else 60)),
            "projects_match": 80 if c.get("github_url") else 50,
            "github_match": min(100, max(20, (c.get("github_commits_last_year") or 0) // 10 + (c.get("github_stars") or 0) * 10)) if c.get("github_url") else 0
        }

    # Strip resume_base64 from insights before sending to frontend
    # (it's served via the dedicated /candidates/{id}/resume endpoint)
    db_insights.pop("resume_base64", None)

    insights = {
        "strengths": c.get("key_strengths") or [],
        "weaknesses": c.get("development_gaps") or [],
        "concerns": c.get("potential_concerns") or [],
        "career_progression": "Stable trajectory",
        **db_insights
    }
    insights["completeness_score"] = float(c.get("completeness_score") or 0.0)
    insights["ats_score"] = float(c.get("ats_score") or 0.0)
    insights["executive_summary"] = db_insights.get("ai_summary", {}).get("executive_summary") or db_insights.get("executive_summary") or c.get("summary") or ""
        
    eval_breakdown = c.get("evaluation_breakdown") or {}
    if isinstance(eval_breakdown, str):
        try:
            import json
            eval_breakdown = json.loads(eval_breakdown)
        except Exception:
            eval_breakdown = {}

    return {
        "id": str(c.get("id")),
        "organization_id": str(c.get("recruiter_id")),
        "name": c.get("full_name") or "Unknown",
        "email": c.get("email") or "",
        "phone": c.get("phone") or "",
        "role": c.get("career_tier") or "Software Engineer",
        "github": github_val,
        "github_stars": c.get("github_stars") or 0,
        "github_languages": c.get("github_languages") or [],
        "github_commits_last_year": c.get("github_commits_last_year") or 0,
        "linkedin": linkedin_val,
        "location": c.get("location") or "Remote",
        "score": round(c.get("match_score", 0.0) or 0.0),
        "blind_score": round(c.get("blind_score", 0.0) or 0.0),
        "status": status,
        "stage": stage_val,
        "summary": summary,
        "experience_years": c.get("experience_years") or 0,
        "resume_text": decrypt_field(c.get("raw_text") or ""),
        "has_resume_file": has_resume,
        "resume_filename": c.get("resume_filename") or "",
        "skills": c.get("skills") or [],
        "experience": experience,
        "job_matches": job_matches,
        "jobMatches": job_matches,
        "radar_data": radar_data,
        "radarData": radar_data,
        "qa": c.get("interview_questions") or [],
        "insights": insights,
        "evaluation_breakdown": eval_breakdown,
        "analyzed_at": c.get("created_at")
    }

# ─── Public API ───

async def fetch_all_candidates(recruiter_id: str = None) -> list[dict]:
    supabase = get_supabase()
    query = supabase.table("candidates").select("*, jobs(title)")
    if recruiter_id:
        query = query.eq("recruiter_id", recruiter_id)
    res = query.execute()
    return [_candidate_to_dict(c) for c in res.data]

async def fetch_candidate_by_id(candidate_id: str, recruiter_id: str = None) -> dict | None:
    supabase = get_supabase()
    query = supabase.table("candidates").select("*, jobs(title)").eq("id", candidate_id)
    if recruiter_id:
        query = query.eq("recruiter_id", recruiter_id)
    res = query.execute()
    return _candidate_to_dict(res.data[0]) if res.data else None

async def delete_candidate(candidate_id: str, recruiter_id: str = None) -> bool:
    supabase = get_supabase()
    query = supabase.table("candidates").delete().eq("id", candidate_id)
    if recruiter_id:
        query = query.eq("recruiter_id", recruiter_id)
    query.execute()
    return True

async def save_candidate(candidate: dict, recruiter_id: str = None) -> dict:
    supabase = get_supabase()
    
    # Map status to pipeline_stage (lowercase)
    status_to_stage = {
        "Analyzing": "analyzing",
        "Screening": "screening",
        "Shortlisted": "shortlisted",
        "Interviewing": "interviewing",
        "Offer": "offer",
        "Hired": "hired",
        "Rejected": "rejected"
    }
    status_str = candidate.get("status", "Screening")
    if status_str == "Analyzing":
        pipeline_stage = "screening"
    else:
        pipeline_stage = status_to_stage.get(status_str, "screening")
    
    # Map jobMatches / job_matches to job_id and match_score
    job_id = None
    match_score = candidate.get("score") or candidate.get("final_score") or 0.0
    job_matches = candidate.get("jobMatches") or candidate.get("job_matches") or []
    if job_matches:
        job_id = job_matches[0].get("job_id")
        match_score = job_matches[0].get("tfidf_score") or match_score
        
    candidate_id = candidate.get("id")
    existing_insights = {}
    if candidate_id:
        try:
            res = supabase.table("candidates").select("insights").eq("id", candidate_id).execute()
            if res.data:
                existing_insights = res.data[0].get("insights") or {}
        except Exception:
            pass

    insights = candidate.get("insights") or {}
    if not isinstance(insights, dict):
        insights = {}
        
    if existing_insights and isinstance(existing_insights, dict):
        for k, v in existing_insights.items():
            if k not in insights or insights[k] is None:
                insights[k] = v

    if "linkedin" in candidate:
        insights["linkedin"] = candidate["linkedin"]
    
    github_val = candidate.get("github") or ""
    if github_val:
        github_val = github_val.strip()
        github_val = re.sub(r"^(?:https?:/?/?)?(?:www\.)?github\.com/", "", github_val, flags=re.IGNORECASE)
        github_val = re.sub(r"^(?:https?:/?/?)?", "", github_val, flags=re.IGNORECASE)
        github_val = github_val.strip("/").replace(" ", "").replace("\t", "")

    github_val = candidate.get("github") or ""
    if github_val:
        github_val = github_val.strip()
        github_val = re.sub(r"^(?:https?:/?/?)?(?:www\.)?github\.com/", "", github_val, flags=re.IGNORECASE)
        github_val = re.sub(r"^(?:https?:/?/?)?", "", github_val, flags=re.IGNORECASE)
        github_val = github_val.strip("/").replace(" ", "").replace("\t", "")

    github_signals = insights.get("github_signals") or {}
    github_stars = int(github_signals.get("total_stars") or candidate.get("github_stars") or 0)
    github_langs = github_signals.get("languages") or candidate.get("github_languages") or []
    commit_freq = github_signals.get("commit_frequency_per_week") or github_signals.get("commit_frequency") or 0
    github_commits = int(commit_freq * 52) if commit_freq else int(candidate.get("github_commits_last_year") or 0)

    db_record = {
        "full_name": candidate.get("name"),
        "email": candidate.get("email"),
        "phone": candidate.get("phone") or "",
        "location": candidate.get("location", "Remote"),
        "career_tier": candidate.get("role", "Software Engineer"),
        "skills": candidate.get("skills") or [],
        "raw_text": encrypt_field(candidate.get("resume_text") or ""),
        "match_score": float(match_score),
        "completeness_score": float(insights.get("completeness_score") or 0.0),
        "ats_score": float(insights.get("ats_score") or 0.0),
        "key_strengths": insights.get("strengths") or [],
        "development_gaps": insights.get("weaknesses") or [],
        "potential_concerns": insights.get("concerns") or [],
        "pipeline_stage": pipeline_stage,
        "stage": pipeline_stage,
        "github_url": github_val,
        "github_stars": github_stars,
        "github_languages": github_langs,
        "github_commits_last_year": github_commits,
        "blind_score": float(candidate.get("blind_score") or match_score),
        "interview_questions": candidate.get("qa") or [],
        "summary": candidate.get("summary"),
        "insights": insights,
        "experience": candidate.get("experience") or [],
        "evaluation_breakdown": candidate.get("evaluation_breakdown") or {}
    }
    
    # Experience years
    if "experience_years" in candidate:
        db_record["experience_years"] = int(candidate["experience_years"])
    elif "experience" in candidate and isinstance(candidate["experience"], list) and candidate["experience"]:
        # check if the items contain raw strings or objects
        db_record["experience_years"] = len(candidate["experience"]) * 2
    else:
        db_record["experience_years"] = int(candidate.get("experience_years") or 0)
        
    # Map recruiter_id
    r_id = recruiter_id or candidate.get("organization_id") or candidate.get("recruiter_id")
    if r_id:
        db_record["recruiter_id"] = r_id
        
    if job_id:
        db_record["job_id"] = job_id
        
    cand_id = candidate.get("id")
    if not cand_id:
        cand_id = str(uuid.uuid4())
    db_record["id"] = cand_id
    
    res = supabase.table("candidates").upsert(db_record).execute()
    return _candidate_to_dict(res.data[0]) if res.data else {}

# ─── Job Mappers ───

def _job_to_dict(j: dict) -> dict:
    if not j:
        return {}
    req_skills = j.get("required_skills")
    if isinstance(req_skills, list):
        j["required_skills"] = ",".join(req_skills)
    j["organization_id"] = j.get("recruiter_id")
    j.setdefault("company", "HireIQ Corp")
    j.setdefault("department", "Engineering")
    j.setdefault("employment_type", "Full-time")
    j.setdefault("location", "Remote")
    j.setdefault("experience_required", j.get("min_experience", 0))
    j.setdefault("salary_range", "")
    j.setdefault("status", "Open")
    return j

async def fetch_all_jobs(recruiter_id: str = None) -> list[dict]:
    supabase = get_supabase()
    query = supabase.table("jobs").select("*")
    if recruiter_id:
        query = query.eq("recruiter_id", recruiter_id)
    res = query.execute()
    return [_job_to_dict(j) for j in res.data]

async def log_analytics_event(event_type: str, payload: dict):
    logger.info(f"Analytics Event: {event_type} - {payload}")

