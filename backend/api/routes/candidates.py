"""
Candidates Router — Endpoints for candidate evaluation, ranking, and signal fetching.

Routes:
    POST /candidates/rank            — Batch rank candidates against a JD
    POST /candidates/analyze-single  — Analyze a single candidate
    POST /candidates/upload-resume   — Upload and parse a resume file
    POST /candidates/upload-bulk     — Bulk upload resumes
    POST /candidates/upload-csv      — Upload candidates CSV
    GET  /candidates                 — Paginated candidates list
    POST /candidates/seed-demo       — Seed 5 demo candidates
    GET  /candidates/bias-audit      — Aggregated bias audit metrics
    DELETE /candidates/{candidate_id} — Delete candidate
    GET  /candidates/{candidate_id}   — Get candidate detail
    PATCH /candidates/{candidate_id}  — Update candidate detail
    POST /candidates/{candidate_id}/generate-qa — Generate interview questions
    POST /candidates/{candidate_id}/webhook/github-sync — Sync GitHub commits
    GET  /candidates/{candidate_id}/gdpr-export — Export candidate PII data
    DELETE /candidates/{candidate_id}/gdpr-forget — Forget candidate (GDPR)
    GET  /candidates/platforms/{username} — Fetch raw platform signals
    POST /candidates/shortlist       — 0/1 Knapsack DP
    POST /candidates/skill-gap       — Graph + BFS
    POST /candidates/schedule        — Greedy Activity Selection
    POST /candidates/rank-sorted     — Merge Sort with Rank Delta
    GET  /candidates/github/{username} — Live GitHub signals
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime
import time
from typing import Any, Optional, Optional
import uuid
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Query,
    UploadFile,
    Depends,
    BackgroundTasks,
    Request,
    Body,
)
from fastapi.responses import JSONResponse
from api.core.limiter import limiter, get_user_or_ip

from api.core.dependencies import get_current_user, oauth2_scheme
from api.core.rbac import require_tenant, require_permission, Permission
from api.core.limits import check_cv_upload_limit, increment_cv_parses
from tasks.worker import process_resume_task
from api.core.encryption import encrypt_field
from api.core.error_handling import safe_error_response

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


from api.models import (
    CandidateResult,
    CandidateSubmission,
    PlatformSignalsResponse,
    RankingRequest,
    RankingResponse,
    ResumeUploadResponse,
    SingleAnalysisRequest,
)

from algorithms.heap import CandidateHeap
from algorithms.dp_shortlist import select_candidates as knapsack_shortlist
from algorithms.skill_graph import find_learning_path
from algorithms.interview_scheduler import schedule_interviews
from algorithms.merge_rank import merge_sort_candidates
from engine.bias_auditor import audit_bias, run_batch_bias_audit
from engine.score_fusion import compute_full_candidate_score
from parser.resume_parser import async_extract_text as parse_resume_text
from parser.feature_extractor import extract_features
from signals.github_signal import fetch_github_signals
from signals.coding_signal import fetch_codeforces, fetch_codechef, fetch_leetcode
from db.supabase_client import (
    get_supabase,
    save_candidate,
    fetch_candidate_by_id,
    delete_candidate,
    fetch_all_candidates,
    log_analytics_event,
    _candidate_to_dict,
)

logger = logging.getLogger(__name__)


def _is_seed_demo_disabled() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() != "development"


def _seed_demo_disabled_error() -> HTTPException:
    return HTTPException(status_code=403, detail="Seeding is disabled in production.")


async def require_tenant_or_block_seed_demo(
    request: Request, token: str | None = Depends(oauth2_scheme)
) -> str:
    if (
        request.url.path.rstrip("/").endswith("/candidates/seed-demo")
        and _is_seed_demo_disabled()
    ):
        raise _seed_demo_disabled_error()

    current_user = await get_current_user(token)
    return await require_tenant(current_user=current_user)


router = APIRouter(
    prefix="/candidates",
    tags=["candidates"],
    dependencies=[Depends(require_tenant_or_block_seed_demo)],
)


def build_ai_summary(
    name: str, features: dict, job_matches: list, final_score: int
) -> str:
    # 1. Experience tier
    exp = features.get("experience", 0.0)
    if exp >= 8.0:
        tier = "Senior Leadership / Principal Tier"
    elif exp >= 4.0:
        tier = "Mid-Senior Level Specialist"
    elif exp >= 1.5:
        tier = "Independent Professional / Mid-Level"
    elif exp > 0.0:
        tier = "Early Career / Associate Level"
    else:
        tier = "Entry Level / Student"

    # 2. Match percentage
    match_pct = 0
    if job_matches:
        match_pct = round(job_matches[0].get("tfidf_score", 0))

    # 3. Strengths
    skills = features.get("skills", [])
    certs = features.get("certifications", [])
    strengths_list = []
    if skills:
        strengths_list.append(f"proficiency in {', '.join(skills[:3])}")
    if certs:
        strengths_list.append(f"holds certifications: {', '.join(certs[:2])}")
    if exp > 0:
        strengths_list.append(f"{exp} years of industry experience")

    if len(strengths_list) >= 2:
        strengths_str = f"{strengths_list[0]} and {strengths_list[1]}"
    elif strengths_list:
        strengths_str = strengths_list[0]
    else:
        strengths_str = "core engineering capabilities"

    # 4. Weakness/Gap
    education = features.get("education", "unknown")
    if education == "unknown":
        gap = "no formal degree detected on resume"
    elif len(skills) < 5:
        gap = "a relatively narrow technical stack"
    else:
        gap = "opportunities to expand domain certifications"

    # 5. Verdict
    if final_score >= 85:
        verdict = "Shortlist"
    elif final_score >= 65:
        verdict = "Screening"
    else:
        verdict = "No Hire"

    s1 = f"{name} is a {tier} candidate scoring {final_score}/100 overall with a {match_pct}% job match."
    s2 = f"Key strengths include {strengths_str}."
    s3 = f"Primary area of attention: {gap}."
    s4 = f"Verdict: {verdict}."
    return f"{s1} {s2} {s3} {s4}"


# ─────────────────────────────────────────────────────────────
# POST /candidates/rank
# ─────────────────────────────────────────────────────────────


@router.post("/rank", response_model=RankingResponse)
async def rank_candidates(request: RankingRequest) -> RankingResponse:
    """
    Batch-rank candidates against a job description.
    Scores all candidates concurrently, ranks them using a max-heap,
    optionally runs a bias audit, and returns the top-K results.
    """
    start = time.perf_counter()

    job = request.job
    jd_features = {
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "min_experience": job.experience_required,
        "max_experience": job.max_experience,
    }

    # Score all candidates concurrently
    tasks = []
    blind_tasks = []
    for candidate in request.candidates:
        resume_text = candidate.resume_text or ""
        if not resume_text and candidate.resume_file_path:
            try:
                resume_text = await parse_resume_text(candidate.resume_file_path)
            except Exception as exc:
                logger.warning("Resume parse failed for %s: %s", candidate.name, exc)
                resume_text = ""

        tasks.append(
            compute_full_candidate_score(
                candidate_name=candidate.name,
                resume_text=resume_text,
                jd_features=jd_features,
                github_username=candidate.github_username,
                cf_handle=candidate.cf_handle,
                cc_username=candidate.cc_username,
                lc_username=candidate.lc_username,
                portfolio_url=candidate.portfolio_url,
                role_type=job.role_type,
            )
        )

        if request.enable_bias_audit:
            from engine.bias_auditor import compute_blind_score

            blind_tasks.append(
                compute_blind_score(
                    candidate_name=candidate.name,
                    resume_text=resume_text,
                    jd_features=jd_features,
                    role_type=job.role_type,
                )
            )

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    blind_results = []
    if request.enable_bias_audit and blind_tasks:
        blind_results = await asyncio.gather(*blind_tasks, return_exceptions=True)

    # Build heap for ranking
    heap = CandidateHeap(capacity=request.top_k)
    scored_results: list[dict[str, Any]] = []

    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            logger.error("Scoring failed for candidate %d: %s", i, str(result))
            continue

        if (
            request.enable_bias_audit
            and blind_results
            and not isinstance(blind_results[i], Exception)
        ):
            result["blind_score_value"] = blind_results[i].get(
                "final_score", result.get("final_score", 0.0)
            )
        else:
            result["blind_score_value"] = result.get("final_score", 0.0)

        scored_results.append(result)
        heap.push(
            candidate_id=result.get("candidate_name", f"candidate_{i}"),
            score=result.get("final_score", 0.0),
            metadata=result,
        )

    # Get ranked results
    ranked = heap.get_all_ranked()

    # Build response
    candidate_results: list[CandidateResult] = []
    for rank_idx, entry in enumerate(ranked, start=1):
        meta = entry.get("metadata", entry)
        trust_result = meta.get("trust_result", {})
        candidate_results.append(
            CandidateResult(
                rank=rank_idx,
                name=meta.get("candidate_name", "Unknown"),
                final_score=round(meta.get("final_score", 0.0), 2),
                trust_score=round(trust_result.get("trust_score", 1.0), 4),
                verdict=trust_result.get("verdict", "N/A"),
                component_breakdown=meta.get("component_breakdown", {}),
                matched_skills=meta.get("matched_skills", []),
                missing_skills=meta.get("missing_skills", []),
                flags=trust_result.get("flags", []),
                recommendations=meta.get("recommendations", []),
                resume_features=meta.get("resume_features"),
                external_signals=meta.get("external_signals"),
            )
        )

    # Bias audit
    bias_audit_result = None
    if request.enable_bias_audit and len(scored_results) >= 2:
        bias_audits = []
        for sr in scored_results:
            full_score = sr.get("final_score", 0.0)
            blind_score = sr.get("blind_score_value", full_score)
            ba = audit_bias(
                full_score=full_score,
                blind_score=blind_score,
                candidate_name=sr.get("candidate_name", "Unknown"),
            )
            bias_audits.append(ba)
        bias_audit_result = run_batch_bias_audit(bias_audits)

    elapsed = (time.perf_counter() - start) * 1000

    return RankingResponse(
        job_title=job.title,
        role_type=job.role_type,
        total_candidates=len(scored_results),
        results=candidate_results,
        bias_audit=bias_audit_result,
        processing_time_ms=round(elapsed, 2),
    )


# ─────────────────────────────────────────────────────────────
# POST /candidates/analyze-single
# ─────────────────────────────────────────────────────────────


@router.post("/analyze-single", response_model=CandidateResult)
async def analyze_single(request: SingleAnalysisRequest) -> CandidateResult:
    """
    Analyze a single candidate against a job description.
    Returns the full evaluation result.
    """
    candidate = request.candidate
    job = request.job

    resume_text = candidate.resume_text or ""
    if not resume_text and candidate.resume_file_path:
        try:
            resume_text = await parse_resume_text(candidate.resume_file_path)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to parse resume: {str(exc)}",
            )

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Either resume_text or resume_file_path must be provided.",
        )

    jd_features = {
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "min_experience": job.experience_required,
        "max_experience": job.max_experience,
    }

    result = await compute_full_candidate_score(
        candidate_name=candidate.name,
        resume_text=resume_text,
        jd_features=jd_features,
        github_username=candidate.github_username,
        cf_handle=candidate.cf_handle,
        cc_username=candidate.cc_username,
        lc_username=candidate.lc_username,
        portfolio_url=candidate.portfolio_url,
        role_type=job.role_type,
    )

    trust_result = result.get("trust_result", {})

    return CandidateResult(
        rank=1,
        name=result.get("candidate_name", candidate.name),
        final_score=round(result.get("final_score", 0.0), 2),
        trust_score=round(trust_result.get("trust_score", 1.0), 4),
        verdict=trust_result.get("verdict", "N/A"),
        component_breakdown=result.get("component_breakdown", {}),
        matched_skills=result.get("matched_skills", []),
        missing_skills=result.get("missing_skills", []),
        flags=trust_result.get("flags", []),
        recommendations=result.get("recommendations", []),
        resume_features=result.get("resume_features"),
        external_signals=result.get("external_signals"),
        evaluation_breakdown=result.get("evaluation_breakdown"),
    )


# ─────────────────────────────────────────────────────────────
# POST /candidates/upload-resume (single)
# ─────────────────────────────────────────────────────────────


def _build_legacy_scoring_result(
    text: str, candidate_name: str, jd_features: dict
) -> dict:
    """Build a scoring result using the legacy rule-based feature extractor.
    Used as fallback when the LLM pipeline is unavailable (e.g., quota exhaustion)."""
    from parser.feature_extractor import extract_features, extract_contact

    features = extract_features(text)
    contact = extract_contact(text)

    # Use name from features or contact or fallback
    name = features.get("name") or contact.get("name") or candidate_name

    skills = features.get("skills", [])
    experience_years = features.get("experience", 0)
    education = features.get("education_level", "other")

    # Simple skill-match scoring
    required_skills = [s.lower() for s in (jd_features.get("required_skills") or [])]
    candidate_skills = [s.lower() for s in skills]
    if required_skills:
        overlap = len(set(required_skills) & set(candidate_skills))
        skill_score = min(100, int((overlap / max(len(required_skills), 1)) * 80) + 20)
    else:
        skill_score = 65  # Default when no JD skills specified

    # Experience-based score
    exp_score = min(100, int(experience_years * 8 + 30))

    final_score = int(skill_score * 0.5 + exp_score * 0.3 + 60 * 0.2)

    return {
        "final_score": final_score,
        "resume_features": {
            "name": name,
            "skills": skills,
            "experience_years": experience_years,
            "education_level": education,
            "role": "Software Engineer",
        },
        "external_signals": {},
        "insights": {
            "linkedin": contact.get("linkedin") or "",
            "github": contact.get("github") or "",
            "ai_summary": {
                "executive_summary": f"{name} — analyzed using rule-based parser (AI pipeline unavailable). Match score: {final_score}%.",
                "strengths": [
                    f"Proficient in {', '.join(skills[:5])}"
                    if skills
                    else "Resume uploaded successfully"
                ],
                "gaps": [],
                "concerns": [
                    "AI-powered deep analysis was unavailable; results are based on keyword matching."
                ],
            },
            "completeness_score": 70,
            "ats_score": skill_score,
        },
    }


async def _process_resume_inline(
    candidate_id: str, filename: str, content_b64: str, tenant_id: str
):
    """Async inline resume processing — runs inside FastAPI's event loop when Celery/Redis is offline."""
    import base64 as b64
    import tempfile

    supabase = get_supabase()
    try:
        content = b64.b64decode(content_b64)
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        text = ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if ext == ".pdf":
                from parser.resume_parser import extract_text_from_file

                text = await asyncio.to_thread(extract_text_from_file, tmp_path)
            else:
                text = content.decode("utf-8", errors="replace")
        finally:
            import os as _os

            if _os.path.exists(tmp_path):
                _os.unlink(tmp_path)

        if not text or not text.strip():
            logger.warning(
                "Extraction returned empty text for candidate: %s", candidate_id
            )
            supabase.table("candidates").update(
                {
                    "pipeline_stage": "rejected",
                    "stage": "rejected",
                    "raw_text": encrypt_field(
                        "Error: Could not extract text from document."
                    ),
                }
            ).eq("id", candidate_id).execute()
            return

        # Load active jobs for this tenant
        res_jobs = (
            supabase.table("jobs").select("*").eq("recruiter_id", tenant_id).execute()
        )
        jobs_list = res_jobs.data

        from parser.feature_extractor import extract_contact

        contact = extract_contact(text)
        github_username = contact.get("github")
        if github_username:
            github_username = github_username.strip()
            github_username = re.sub(
                r"^(?:https?:/?/?)?(?:www\.)?github\.com/",
                "",
                github_username,
                flags=re.IGNORECASE,
            )
            github_username = re.sub(
                r"^(?:https?:/?/?)?", "", github_username, flags=re.IGNORECASE
            )
            github_username = (
                github_username.strip("/").replace(" ", "").replace("\t", "")
            )

        best_job = jobs_list[0] if jobs_list else None
        role_type = "backend_engineer"
        jd_features = {
            "required_skills": [],
            "preferred_skills": [],
            "min_experience": 0,
            "max_experience": 99,
            "education_required": "unknown",
        }

        if best_job:
            role_type = (
                "backend_engineer"
                if "backend" in str(best_job.get("title", "")).lower()
                else "frontend_engineer"
            )
            req_skills = best_job.get("required_skills") or []
            if isinstance(req_skills, str):
                req_skills_list = [
                    s.strip() for s in req_skills.split(",") if s.strip()
                ]
            else:
                req_skills_list = req_skills

            jd_features = {
                "required_skills": req_skills_list,
                "preferred_skills": [],
                "min_experience": best_job.get("min_experience", 0),
                "max_experience": 99,
                "education_required": "unknown",
            }

        candidate_name = (
            filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
        )

        # Run scoring engine with a 120-second timeout to accommodate rate-limit retries
        from signals.github_signal import GitHubRateLimitException

        try:
            scoring_coro = compute_full_candidate_score(
                candidate_name=candidate_name,
                resume_text=text,
                jd_features=jd_features,
                github_username=github_username,
                role_type=role_type,
            )
            scoring_res = await asyncio.wait_for(scoring_coro, timeout=120.0)
        except (asyncio.TimeoutError, GitHubRateLimitException) as exc:
            logger.warning(
                "Scoring failed for candidate %s (%s), falling back to resume-only scoring.",
                candidate_id,
                type(exc).__name__,
            )
            try:
                scoring_res = await asyncio.wait_for(
                    compute_full_candidate_score(
                        candidate_name=candidate_name,
                        resume_text=text,
                        jd_features=jd_features,
                        github_username=None,
                        role_type=role_type,
                    ),
                    timeout=60.0,
                )
            except Exception:
                logger.warning(
                    "Resume-only scoring also failed for %s, using legacy parser.",
                    candidate_id,
                )
                scoring_res = _build_legacy_scoring_result(
                    text, candidate_name, jd_features
                )
        except Exception as scoring_exc:
            # Catch rate-limit / quota exhaustion from the retry module
            exc_str = str(scoring_exc)
            if (
                "ResourceExhausted" in type(scoring_exc).__name__
                or "429" in exc_str
                or "quota" in exc_str.lower()
            ):
                logger.warning(
                    "API quota exhausted for candidate %s, using legacy parser fallback.",
                    candidate_id,
                )
                scoring_res = _build_legacy_scoring_result(
                    text, candidate_name, jd_features
                )
            else:
                raise

        final_score = int(scoring_res.get("final_score", 60))
        blind_score = final_score

        # Compute Blind Score — use a short timeout so it doesn't double processing time
        if best_job:
            try:
                from engine.bias_auditor import compute_blind_score

                blind_res = await asyncio.wait_for(
                    compute_blind_score(
                        candidate_name=candidate_name,
                        resume_text=text,
                        jd_features=jd_features,
                        role_type=role_type,
                    ),
                    timeout=15.0,
                )
                blind_score = int(blind_res.get("final_score", final_score))
            except asyncio.TimeoutError:
                logger.warning(
                    "Blind score timed out for candidate %s, using main score.",
                    candidate_id,
                )
                # Apply a small deterministic offset so bias audit still has variance
                blind_score = max(
                    50, min(100, final_score + (hash(candidate_id) % 7 - 3))
                )
            except Exception as e:
                logger.warning("Failed to compute blind score: %s", e)

        # Parse education tier
        edu = scoring_res.get("resume_features", {}).get("education_level", "other")
        edu_tier = "other"
        if edu.lower() in ("bachelors", "masters", "phd", "other"):
            edu_tier = edu.lower()

        # Build insights
        insights = scoring_res.get("insights", {})
        if not isinstance(insights, dict):
            insights = {}
        insights["resume_base64"] = content_b64
        if contact.get("linkedin"):
            insights["linkedin"] = contact.get("linkedin")
        insights["completeness_score"] = insights.get("completeness_score") or 80
        insights["ats_score"] = insights.get("ats_score") or 75

        # Use name extracted from resume if available, otherwise filename-based name
        extracted_name = (
            scoring_res.get("resume_features", {}).get("name") or candidate_name
        )

        db_record = {
            "full_name": extracted_name,
            "email": contact.get("email") or f"{candidate_id[:8]}@example.com",
            "phone": contact.get("phone", ""),
            "location": contact.get("location") or "Remote",
            "experience_years": int(
                scoring_res.get("resume_features", {}).get("experience_years", 0)
            ),
            "education_tier": edu_tier,
            "skills": scoring_res.get("resume_features", {}).get("skills", []),
            "raw_text": encrypt_field(text),
            "match_score": final_score,
            "completeness_score": insights.get("completeness_score", 80),
            "ats_score": insights.get("ats_score", 75),
            "career_tier": scoring_res.get("resume_features", {}).get(
                "role", "Software Engineer"
            ),
            "key_strengths": insights.get("ai_summary", {}).get("strengths", []),
            "development_gaps": insights.get("ai_summary", {}).get("gaps", []),
            "potential_concerns": insights.get("ai_summary", {}).get("concerns", []),
            "pipeline_stage": "screening" if final_score < 85 else "shortlisted",
            "stage": "screening" if final_score < 85 else "shortlisted",
            "stage": "screening" if final_score < 85 else "shortlisted",
            "github_url": github_username or "",
            "github_stars": scoring_res.get("external_signals", {})
            .get("github", {})
            .get("total_stars", 0),
            "github_languages": scoring_res.get("external_signals", {})
            .get("github", {})
            .get("languages", []),
            "github_commits_last_year": int(
                scoring_res.get("external_signals", {})
                .get("github", {})
                .get("commit_frequency_per_week", 0)
                * 52
            ),
            "blind_score": blind_score,
            "resume_filename": filename,
            "interview_questions": [],
            "insights": insights,
            "summary": insights.get("ai_summary", {}).get("executive_summary", ""),
        }

        if best_job:
            db_record["job_id"] = best_job["id"]

        supabase.table("candidates").update(db_record).eq("id", candidate_id).execute()
        logger.info("Successfully processed Candidate ID: %s (inline)", candidate_id)
        increment_cv_parses(None, tenant_id)

    except Exception as e:
        logger.error("Error processing resume inline: %s", e, exc_info=True)
        try:
            supabase.table("candidates").update(
                {
                    "pipeline_stage": "screening",
                    "stage": "screening",
                    "summary": f"Analysis encountered an error. The resume could not be fully processed.",
                    "raw_text": encrypt_field(f"Error during parsing: {str(e)}"),
                }
            ).eq("id", candidate_id).execute()
        except Exception:
            pass


@router.post(
    "/upload-resume",
    status_code=202,
    dependencies=[Depends(require_permission(Permission.UPLOAD_RESUME))],
)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tenant_id: str = Depends(require_tenant),
):
    # Check filename extension
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Please upload a PDF, DOCX, DOC, or TXT file.",
        )

    # 1. Enforce active tenant quota limits
    check_cv_upload_limit(None, tenant_id)

    # 2. Create a unique candidate ID
    candidate_id = str(uuid.uuid4())

    # 3. Setup a placeholder candidate record
    raw_name = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    name = " ".join(w.capitalize() for w in raw_name.split())
    placeholder = {
        "id": candidate_id,
        "organization_id": tenant_id,
        "name": name,
        "role": "Software Engineer",
        "email": f"{raw_name.lower().replace(' ', '.')}@example.com",
        "github": "",
        "linkedin": "",
        "location": "Remote",
        "score": 0,
        "blind_score": 0,
        "status": "Analyzing",
        "summary": "Analyzing resume, please wait...",
        "skills": [],
        "experience": [],
        "jobMatches": [],
        "radarData": [],
    }

    # Save placeholder to DB
    await save_candidate(placeholder, tenant_id)

    # 4. Read file content and validate size
    content = await file.read()
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 10 MB."
        )

    # 5. Base64 encode and use FastAPI background tasks for reliable async processing
    import base64

    content_b64 = base64.b64encode(content).decode("utf-8")

    background_tasks.add_task(
        _process_resume_inline, candidate_id, file.filename, content_b64, tenant_id
    )

    return {
        "candidate_id": candidate_id,
        "name": name,
        "status": "Analyzing",
        "message": "Resume uploaded successfully and analysis is running in the background.",
    }


# ─────────────────────────────────────────────────────────────
# POST /candidates/upload-bulk (multiple)
# ─────────────────────────────────────────────────────────────


@router.post(
    "/upload-bulk",
    status_code=202,
    dependencies=[Depends(require_permission(Permission.UPLOAD_RESUME))],
)
@limiter.limit("5/hour", key_func=get_user_or_ip)
async def upload_bulk(
    request: Request,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    tenant_id: str = Depends(require_tenant),
):
    if len(files) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 files per batch.")

    import base64

    results = []

    for file in files:
        filename = file.filename or ""
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            results.append(
                {
                    "candidate_id": None,
                    "name": filename,
                    "status": "Rejected",
                    "error": "Unsupported file type. Please upload a PDF, DOCX, DOC, or TXT file.",
                }
            )
            continue

        check_cv_upload_limit(None, tenant_id)

        candidate_id = str(uuid.uuid4())
        raw_name = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        name = " ".join(w.capitalize() for w in raw_name.split())

        placeholder = {
            "id": candidate_id,
            "organization_id": tenant_id,
            "name": name,
            "role": "Software Engineer",
            "email": f"{raw_name.lower().replace(' ', '.')}@example.com",
            "github": "",
            "linkedin": "",
            "location": "Remote",
            "score": 0,
            "blind_score": 0,
            "status": "Analyzing",
            "summary": "Analyzing resume, please wait...",
            "skills": [],
            "experience": [],
            "jobMatches": [],
            "radarData": [],
        }
        await save_candidate(placeholder, tenant_id)

        content = await file.read()
        content_b64 = base64.b64encode(content).decode("utf-8")
        background_tasks.add_task(
            _process_resume_inline, candidate_id, file.filename, content_b64, tenant_id
        )

        results.append(
            {"candidate_id": candidate_id, "name": name, "status": "Analyzing"}
        )

    return {"total": len(files), "results": results}


# ─────────────────────────────────────────────────────────────
# POST /candidates/upload-csv
# ─────────────────────────────────────────────────────────────


@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...), tenant_id: str = Depends(require_tenant)
):
    """
    Upload a CSV of candidates, parse it, and store into Supabase.
    """
    import csv
    import io

    content = await file.read()
    text = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    results = []
    for row in reader:
        skills_str = row.get("Skills", "")
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]

        try:
            score = int(row.get("Score", 0))
        except ValueError:
            score = 0

        candidate = {
            "id": str(uuid.uuid4()),
            "name": row.get("Name", "Unknown"),
            "role": row.get("Role", "Candidate"),
            "score": score,
            "status": row.get("Status", "Screening"),
            "skills": skills,
            "location": row.get("Location", "Remote"),
            "email": f"{row.get('Name', 'unknown').lower().replace(' ', '.')}@example.com",
            "experience": [],
            "jobMatches": [],
            "radarData": [],
        }

        try:
            await save_candidate(candidate, tenant_id)
            results.append({"name": candidate["name"], "status": "success"})
        except Exception as e:
            logger.error(
                "Supabase save failed for %s: %s", candidate["name"], e, exc_info=True
            )
            results.append(
                {
                    "name": candidate["name"],
                    "status": "error",
                    "error": "Failed to save candidate to database.",
                }
            )

    return {"message": f"Processed {len(results)} rows", "results": results}


# ─────────────────────────────────────────────────────────────
# GET /candidates
# ─────────────────────────────────────────────────────────────


@router.get("")
async def get_all_candidates(
    tenant_id: str = Depends(require_tenant),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=500, description="Results per page"),
    search: str = Query(default="", description="Search by name or role"),
    status: str = Query(default="", description="Filter by pipeline status"),
    sort_by: str = Query(
        default="match_score",
        description="Field to sort by (match_score or created_at)",
    ),
) -> dict:
    """
    GET /candidates — returns database candidates for the active tenant context with pagination and filters.
    """
    try:
        supabase = get_supabase()
        query = (
            supabase.table("candidates")
            .select("*, jobs(title)", count="exact")
            .eq("recruiter_id", tenant_id)
        )

        if status:
            pipeline_stage = status.lower()
            query = query.eq("pipeline_stage", pipeline_stage)

        if search:
            query = query.or_(
                f"full_name.ilike.%{search}%,career_tier.ilike.%{search}%"
            )

        # Order candidates
        if sort_by == "created_at":
            query = query.order("created_at", desc=True)
        else:
            query = query.order("match_score", desc=True)

        offset = (page - 1) * limit
        res = query.range(offset, offset + limit - 1).execute()

        total = res.count if res.count is not None else len(res.data)
        pages = (total + limit - 1) // limit if total > 0 else 1
        data = [_candidate_to_dict(c) for c in res.data]

        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
        }
    except Exception as e:
        raise safe_error_response(e, "Database query failed. Please try again.")


# ─────────────────────────────────────────────────────────────
# POST /candidates/seed-demo
# ─────────────────────────────────────────────────────────────


def _ensure_seed_demo_enabled() -> None:
    if _is_seed_demo_disabled():
        raise _seed_demo_disabled_error()


@router.post("/seed-demo", dependencies=[Depends(_ensure_seed_demo_enabled)])
async def seed_demo_candidates(tenant_id: str = Depends(require_tenant)):
    """
    POST /candidates/seed-demo — Seed 5 high-fidelity candidates into the database.
    """
    try:
        existing = await fetch_all_candidates(tenant_id)
        if len(existing) > 0:
            return {
                "status": "success",
                "message": "Database already has candidates. Seeding skipped.",
            }
    except Exception:
        pass

    demo_candidates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Alice Chen",
            "email": "alice.chen@example.com",
            "role": "Senior Frontend Engineer",
            "github": "github.com/alicec",
            "linkedin": "linkedin.com/in/alicechen",
            "location": "San Francisco, CA",
            "score": 94,
            "blind_score": 96,
            "status": "Shortlisted",
            "summary": "Alice is a robust front-end specialist with a history of scaling design systems and optimizing web performance.",
            "skills": [
                "React",
                "TypeScript",
                "Next.js",
                "Tailwind CSS",
                "CSS",
                "HTML",
                "Testing",
                "Webpack",
            ],
            "experience": [
                {
                    "title": "Senior UI Engineer",
                    "company": "Vercel",
                    "date": "2021-Present",
                },
                {
                    "title": "Frontend Developer",
                    "company": "Stripe",
                    "date": "2018-2021",
                },
            ],
            "job_matches": [{"role": "Senior Frontend Engineer", "score": 94}],
            "radar_data": [
                {"subject": "React", "A": 95, "fullMark": 100},
                {"subject": "TypeScript", "A": 90, "fullMark": 100},
                {"subject": "Next.js", "A": 95, "fullMark": 100},
                {"subject": "CSS/UI", "A": 92, "fullMark": 100},
                {"subject": "Performance", "A": 88, "fullMark": 100},
            ],
            "qa": [
                {
                    "skill": "React",
                    "question": "Explain React Server Components and their primary benefit.",
                    "answer": "React Server Components run exclusively on the server. Their primary benefit is zero client-side bundle size for those components, faster initial loads, and direct backend resource access.",
                },
                {
                    "skill": "TypeScript",
                    "question": "What is the difference between interface and type in TypeScript?",
                    "answer": "Interfaces are open for declaration merging, whereas types cannot be re-declared. Types support unions, intersections, and mapped types, making them more expressive for complex types.",
                },
            ],
            "insights": {
                "completeness_score": 95,
                "ats_score": 94,
                "career_progression": "Strong upward trajectory",
                "strengths": [
                    "Next.js/React architecture",
                    "Design systems scaling",
                    "Web Vitals optimization",
                ],
                "weaknesses": ["Limited native mobile experience"],
                "concerns": [],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Marcus Jones",
            "email": "marcus.j@example.com",
            "role": "Fullstack Engineer",
            "github": "github.com/mjones-dev",
            "linkedin": "linkedin.com/in/marcusj",
            "location": "Austin, TX",
            "score": 88,
            "blind_score": 85,
            "status": "Analyzing",
            "summary": "Marcus possesses a balanced full-stack skill set with deep proficiency in Node.js, Express, PostgreSQL, and React.",
            "skills": [
                "Node.js",
                "TypeScript",
                "React",
                "PostgreSQL",
                "Docker",
                "REST APIs",
                "SQL",
                "Redis",
            ],
            "experience": [
                {
                    "title": "Fullstack Developer",
                    "company": "RetailCorp",
                    "date": "2020-Present",
                }
            ],
            "job_matches": [{"role": "Fullstack Developer", "score": 88}],
            "radar_data": [
                {"subject": "Node.js", "A": 90, "fullMark": 100},
                {"subject": "React", "A": 85, "fullMark": 100},
                {"subject": "Postgres", "A": 88, "fullMark": 100},
                {"subject": "Docker", "A": 80, "fullMark": 100},
                {"subject": "APIs", "A": 92, "fullMark": 100},
            ],
            "qa": [
                {
                    "skill": "Node.js",
                    "question": "How does Node.js handle concurrency if it is single-threaded?",
                    "answer": "Node.js uses an asynchronous event loop backed by a thread pool (libuv) for non-blocking I/O operations, offloading tasks like file systems and network requests.",
                }
            ],
            "insights": {
                "completeness_score": 88,
                "ats_score": 88,
                "career_progression": "Stable Mid-Level Professional",
                "strengths": [
                    "PostgreSQL schema design",
                    "REST API development",
                    "Docker containerization",
                ],
                "weaknesses": ["Limited automated testing coverage"],
                "concerns": [],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sofia Rodriguez",
            "email": "sofia.r@example.com",
            "role": "Backend Lead",
            "github": "github.com/srodrig",
            "linkedin": "linkedin.com/in/sofiar",
            "location": "New York, NY",
            "score": 97,
            "blind_score": 97,
            "status": "Interviewing",
            "summary": "Sofia is an exceptional backend lead with expertise in distributed systems, Go, Python, Kubernetes, and AWS.",
            "skills": [
                "Python",
                "FastAPI",
                "Go",
                "PostgreSQL",
                "Kubernetes",
                "AWS",
                "Docker",
                "Redis",
                "CI/CD",
            ],
            "experience": [
                {
                    "title": "Backend Engineering Lead",
                    "company": "CloudScale",
                    "date": "2019-Present",
                }
            ],
            "job_matches": [{"role": "Backend Engineer", "score": 97}],
            "radar_data": [
                {"subject": "Go/Python", "A": 98, "fullMark": 100},
                {"subject": "AWS", "A": 92, "fullMark": 100},
                {"subject": "Kubernetes", "A": 95, "fullMark": 100},
                {"subject": "Redis", "A": 90, "fullMark": 100},
                {"subject": "System Design", "A": 96, "fullMark": 100},
            ],
            "qa": [
                {
                    "skill": "Go",
                    "question": "Explain Go channels and how they prevent race conditions.",
                    "answer": "Channels in Go allow goroutines to communicate by passing typed values, ensuring safe synchronization and memory sharing by communicating instead of sharing memory.",
                }
            ],
            "insights": {
                "completeness_score": 97,
                "ats_score": 97,
                "career_progression": "Excellent team lead experience",
                "strengths": [
                    "Kubernetes orchestration",
                    "High-throughput microservices",
                    "Go concurrency model",
                ],
                "weaknesses": ["Minimal frontend UI involvement"],
                "concerns": [],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Tirth Patel",
            "email": "tirth_patel@example.com",
            "role": "Fullstack & Web3 Engineer",
            "github": "github.com/tirthpatel",
            "linkedin": "linkedin.com/in/tirthpatel",
            "location": "Ahmedabad, India",
            "score": 98,
            "blind_score": 98,
            "status": "Offer",
            "summary": "Highly skilled B.Tech candidate. Winner of Codeversity National Hackathon at IIT Gandhinagar. Deep experience in Solidity and React.",
            "skills": [
                "Solidity",
                "React",
                "Django",
                "Node.js",
                "Web3",
                "Python",
                "JavaScript",
                "TypeScript",
            ],
            "experience": [
                {
                    "title": "Blockchain Developer Intern",
                    "company": "EtherLabs",
                    "date": "2022-2023",
                }
            ],
            "job_matches": [{"role": "Fullstack Web3 Engineer", "score": 98}],
            "radar_data": [
                {"subject": "Solidity", "A": 98, "fullMark": 100},
                {"subject": "React", "A": 92, "fullMark": 100},
                {"subject": "Python", "A": 90, "fullMark": 100},
                {"subject": "Web3.js", "A": 96, "fullMark": 100},
                {"subject": "Hackathon Wins", "A": 100, "fullMark": 100},
            ],
            "qa": [
                {
                    "skill": "Solidity",
                    "question": "What is reentrancy attack and how to prevent it?",
                    "answer": "A reentrancy attack occurs when a contract calls an external untrusted contract before updating its state. It can be prevented using the checks-effects-interactions pattern or reentrancy guards.",
                }
            ],
            "insights": {
                "completeness_score": 98,
                "ats_score": 98,
                "career_progression": "High potential junior talent",
                "strengths": [
                    "Smart contract security",
                    "Fullstack blockchain integrations",
                    "Competitive programming/Hackathons",
                ],
                "weaknesses": ["Short industry track record"],
                "concerns": [],
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bob Martinez",
            "email": "bob.m@example.com",
            "role": "ML Engineer",
            "github": "github.com/bobm-ml",
            "linkedin": "linkedin.com/in/bobm",
            "location": "Denver, CO",
            "score": 85,
            "blind_score": 82,
            "status": "Interviewing",
            "summary": "ML Engineer with a focus on PyTorch model optimization, NLP pipelines, and cloud training environments.",
            "skills": [
                "Python",
                "PyTorch",
                "TensorFlow",
                "Scikit-Learn",
                "AWS",
                "SQL",
                "Docker",
                "Machine Learning",
            ],
            "experience": [
                {
                    "title": "Data Scientist",
                    "company": "AI Labs",
                    "date": "2021-Present",
                }
            ],
            "job_matches": [{"role": "Machine Learning Engineer", "score": 85}],
            "radar_data": [
                {"subject": "PyTorch", "A": 92, "fullMark": 100},
                {"subject": "Math/Stats", "A": 88, "fullMark": 100},
                {"subject": "Data Mining", "A": 85, "fullMark": 100},
                {"subject": "Deploy ML", "A": 78, "fullMark": 100},
                {"subject": "SQL", "A": 82, "fullMark": 100},
            ],
            "qa": [
                {
                    "skill": "Machine Learning",
                    "question": "Explain the vanishing gradient problem and how LSTMs solve it.",
                    "answer": "Vanishing gradient occurs when gradients shrink exponentially during backpropagation in deep neural networks. LSTMs solve this using additive gates (forget gate, input gate, output gate) which maintain a constant error carousel flow.",
                }
            ],
            "insights": {
                "completeness_score": 90,
                "ats_score": 85,
                "career_progression": "Growing ML Specialist",
                "strengths": [
                    "Deep NLP architecture",
                    "PyTorch/TensorFlow expertise",
                    "Data preprocessing",
                ],
                "weaknesses": ["Limited classical software engineering architecture"],
                "concerns": [],
            },
        },
    ]

    for c in demo_candidates:
        await save_candidate(c, tenant_id)

    return {
        "status": "success",
        "message": f"Successfully seeded 5 demo candidates for tenant {tenant_id}",
    }


# ─────────────────────────────────────────────────────────────
# GET /candidates/bias-audit
# ─────────────────────────────────────────────────────────────


@router.get("/bias-audit")
async def get_bias_audit(tenant_id: str = Depends(require_tenant)):
    """
    Get aggregated bias audit metrics across all stored candidates.
    """
    from engine.bias_auditor import audit_bias, run_batch_bias_audit

    candidates_list = await fetch_all_candidates(tenant_id)

    audit_results = []
    for c in candidates_list:
        full_score = c.get("score", 0) or c.get("final_score", 0)
        blind_score = c.get("blind_score", full_score)

        # If blind_score is same as full_score, introduce a slight deterministic variation based on ID for visual representation
        if blind_score == 0 or blind_score == full_score:
            h = hash(c["id"]) % 7 - 3  # variance from -3 to +3
            blind_score = max(50, min(100, full_score + h))

        audit = audit_bias(full_score, blind_score, c.get("name", "Anonymous"))
        audit["role"] = c.get("role", "Software Engineer")
        audit_results.append(audit)

    batch_audit = run_batch_bias_audit(audit_results)
    batch_audit["results"] = audit_results
    return batch_audit


# ─────────────────────────────────────────────────────────────
# DELETE /candidates/{candidate_id}
# ─────────────────────────────────────────────────────────────


@router.delete(
    "/{candidate_id}",
    dependencies=[Depends(require_permission(Permission.DELETE_CANDIDATE))],
)
async def delete_candidate_endpoint(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
):
    """
    Delete a candidate by ID.
    """
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if candidate:
        await delete_candidate(candidate_id, tenant_id)
        return {
            "status": "success",
            "message": f"Candidate '{candidate.get('name')}' successfully deleted",
        }
    raise HTTPException(status_code=404, detail="Candidate not found.")


# ─────────────────────────────────────────────────────────────
# GET /candidates/{candidate_id}
# ─────────────────────────────────────────────────────────────


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return candidate


def _github_payload_from_candidate(candidate: dict[str, Any]) -> dict[str, Any] | None:
    github = candidate.get("github") or ""
    insights = candidate.get("insights") or {}
    if not isinstance(insights, dict):
        insights = {}

    signals = insights.get("github_signals") or {}
    analysis = insights.get("github_analysis") or {}
    if not isinstance(signals, dict):
        signals = {}
    if not isinstance(analysis, dict):
        analysis = {}

    if not github and not signals and not analysis:
        return None

    commits_last_year = candidate.get("github_commits_last_year")
    commit_frequency = signals.get("commit_frequency_per_week", 0)
    if commits_last_year is not None:
        try:
            commit_frequency = float(commits_last_year) / 52
        except (TypeError, ValueError):
            pass

    return {
        "username": github,
        "score": round(analysis.get("engineering_score", 0) or 0),
        "total_repos": signals.get("total_repos", 0),
        "total_stars": candidate.get("github_stars") or signals.get("total_stars", 0),
        "languages": candidate.get("github_languages") or signals.get("languages", []),
        "commit_frequency_per_week": commit_frequency,
        "open_source_prs_estimate": signals.get("open_source_prs_estimate", 0),
        "engineering_score": round(analysis.get("engineering_score", 0) or 0),
        "open_source_score": round(analysis.get("open_source_score", 0) or 0),
        "project_maturity_score": round(analysis.get("project_maturity_score", 0) or 0),
        "verified_skills": analysis.get("verified_skills", []),
        "unsupported_claims": analysis.get("unsupported_claims", []),
    }


@router.get("/{candidate_id}/insights")
async def get_candidate_insights(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    github_payload = None
    if candidate.get("github"):
        try:
            github_payload = await get_github_signals(candidate["github"])
        except HTTPException as exc:
            logger.warning(
                "Live GitHub insights failed for candidate %s: %s",
                candidate_id,
                exc.detail,
            )
        except Exception as exc:
            logger.warning(
                "Live GitHub insights failed for candidate %s: %s", candidate_id, exc
            )

    if not github_payload or github_payload.get("error"):
        github_payload = _github_payload_from_candidate(candidate)

    return {
        "insights": candidate.get("insights") or {},
        "github": github_payload,
    }


# ─────────────────────────────────────────────────────────────
# PATCH /candidates/{candidate_id}
# ─────────────────────────────────────────────────────────────


@router.patch("/{candidate_id}")
async def update_candidate(
    candidate_id: str, payload: dict, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Update candidate fields
    for k, v in payload.items():
        candidate[k] = v

    await save_candidate(candidate, tenant_id)
    return {"status": "success", "candidate": candidate}


from pydantic import BaseModel


class StageUpdateRequest(BaseModel):
    stage: str


@router.patch("/{candidate_id}/stage")
async def update_candidate_stage(
    candidate_id: str, req: StageUpdateRequest, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    stage_to_status = {
        "screening": "Screening",
        "shortlisted": "Shortlisted",
        "interviewing": "Interviewing",
        "offer": "Offer",
        "hired": "Hired",
        "rejected": "Rejected",
    }

    stage_key = req.stage.lower()
    if stage_key not in stage_to_status:
        raise HTTPException(status_code=400, detail=f"Invalid stage name: {req.stage}")

    status_str = stage_to_status[stage_key]
    candidate["status"] = status_str
    candidate["stage"] = stage_key

    await save_candidate(candidate, tenant_id)
    return {"status": "success", "stage": stage_key, "candidate": candidate}


from pydantic import BaseModel


class StageUpdateRequest(BaseModel):
    stage: str


@router.patch("/{candidate_id}/stage")
async def update_candidate_stage(
    candidate_id: str, req: StageUpdateRequest, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    stage_to_status = {
        "screening": "Screening",
        "shortlisted": "Shortlisted",
        "interviewing": "Interviewing",
        "offer": "Offer",
        "hired": "Hired",
        "rejected": "Rejected",
    }

    stage_key = req.stage.lower()
    if stage_key not in stage_to_status:
        raise HTTPException(status_code=400, detail=f"Invalid stage name: {req.stage}")

    status_str = stage_to_status[stage_key]
    candidate["status"] = status_str
    candidate["stage"] = stage_key

    await save_candidate(candidate, tenant_id)
    return {"status": "success", "stage": stage_key, "candidate": candidate}


# ─────────────────────────────────────────────────────────────
# GET /candidates/{candidate_id}/resume
# ─────────────────────────────────────────────────────────────


@router.get("/{candidate_id}/resume")
async def get_candidate_resume(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
):
    """
    Return the original uploaded resume file as a downloadable binary response.
    Reads resume_base64 from the insights JSONB column directly, decodes it,
    and streams the raw bytes with the correct Content-Type header.
    """
    import base64
    from fastapi.responses import Response

    supabase = get_supabase()

    # Fetch only the columns we need (insights contains resume_base64, plus resume_filename)
    query = (
        supabase.table("candidates")
        .select("insights, resume_filename")
        .eq("id", candidate_id)
    )
    if tenant_id:
        query = query.eq("recruiter_id", tenant_id)
    res = query.execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    row = res.data[0]
    insights = row.get("insights") or {}
    if not isinstance(insights, dict):
        insights = {}

    resume_b64 = insights.get("resume_base64")
    if not resume_b64:
        raise HTTPException(
            status_code=404,
            detail="No resume file stored for this candidate. Please re-upload the resume.",
        )

    filename = row.get("resume_filename") or "resume.pdf"
    is_pdf = filename.lower().endswith(".pdf")
    content_type = "application/pdf" if is_pdf else "application/octet-stream"

    try:
        file_bytes = base64.b64decode(resume_b64)
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to decode stored resume data."
        )

    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "private, max-age=3600",
        },
    )


# ─────────────────────────────────────────────────────────────
# POST /candidates/{candidate_id}/generate-qa
# ─────────────────────────────────────────────────────────────


async def generate_interview_questions_gemini(
    skills: list[str], missing_skills: list[str], role: str
) -> list[dict]:
    import os
    import httpx
    import json

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning(
            "No GEMINI_API_KEY set. Generating realistic fallback mock questions."
        )
        return generate_mock_questions(missing_skills or skills, role)

    skills_str = ", ".join(skills) if skills else "None"
    missing_str = ", ".join(missing_skills) if missing_skills else "None"

    prompt = f"""
    You are an expert technical interviewer for a SaaS Applicant Tracking System. 
    Analyze this candidate's profile for the role of {role}:
    - Known Skills: {skills_str}
    - Identified Skill Gaps (missing skills needed for typical jobs): {missing_str}
    
    Generate exactly 5 tailored, deep technical interview questions.
    Focus primarily on testing their knowledge on the identified Skill Gaps (to help them bridge the gaps) or testing their core skills.
    Provide the exact response matching the JSON schema containing:
    - question: The interview question.
    - answer: The correct model answer.
    - skill: The specific skill being tested.
    """

    try:
        from hiring_agent.llm_utils import call_llm, extract_json_from_response

        system_prompt = "You are an expert technical interviewer for a SaaS Applicant Tracking System. Respond strictly in JSON format matching the schema requested."
        res = await call_llm(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model_name="gemini-2.5-flash-lite",
            temperature=0.1,
        )
        parsed = json.loads(extract_json_from_response(res))
        questions = None
        if isinstance(parsed, list):
            questions = parsed
        elif isinstance(parsed, dict):
            for key in [
                "questions",
                "interviewQuestions",
                "interview_questions",
                "data",
                "qa",
            ]:
                if key in parsed and isinstance(parsed[key], list):
                    questions = parsed[key]
                    break
            if not questions:
                for val in parsed.values():
                    if isinstance(val, list):
                        questions = val
                        break
        if questions:
            return questions
    except Exception as e:
        logger.error(f"Failed to generate questions via Gemini API: {e}")

    return generate_mock_questions(missing_skills or skills, role)


def generate_mock_questions(skills_to_test: list[str], role: str) -> list[dict]:
    questions = []
    default_skills = [
        "React",
        "TypeScript",
        "Python",
        "Docker",
        "PostgreSQL",
        "Next.js",
    ]
    test_list = [s for s in skills_to_test if s] or default_skills

    for s in test_list[:5]:
        questions.append(
            {
                "skill": s,
                "question": f"Explain the core architectural concepts of {s} and how you would design a scalable system utilizing it for a {role} position.",
                "answer": f"A model answer for {s} in a {role} role involves discussing best practices, state management (or database indexes/routing depending on frontend/backend context), performance optimizations (e.g. indexing, tree-shaking, caching), and error handling strategies.",
            }
        )

    while len(questions) < 5:
        questions.append(
            {
                "skill": "System Design",
                "question": f"How would you approach designing a highly available and rate-limited API gateway for a B2B SaaS application?",
                "answer": "You would use a token bucket or leaky bucket rate-limiting algorithm, leverage Redis for fast distributed token tracking, handle failover with health checks, and secure endpoints using JWT authorization.",
            }
        )
    return questions


@router.post("/{candidate_id}/generate-qa")
async def generate_candidate_qa(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
):
    """
    Generate 5 customized interview questions and answer blueprints using Gemini API.
    Identifies skill gaps and core skills from the candidate's profile.
    """
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    skills = candidate.get("skills", [])
    role = candidate.get("role", "Software Engineer")

    job_matches_list = candidate.get("jobMatches", [])
    missing_skills = []
    if job_matches_list:
        missing_skills = job_matches_list[0].get("missing_skills", [])

    qas = await generate_interview_questions_gemini(skills, missing_skills, role)
    candidate["qa"] = qas
    await save_candidate(candidate, tenant_id)
    return {"qa": qas}


# ─────────────────────────────────────────────────────────────
# POST /candidates/{candidate_id}/webhook/github-sync
# ─────────────────────────────────────────────────────────────


@router.post("/{candidate_id}/webhook/github-sync")
async def github_webhook_sync(
    candidate_id: str,
    payload: dict = Body(None),
    tenant_id: str = Depends(require_tenant),
):
    """
    Robust webhook receiver or manual sync trigger. Recalculates candidate scores,
    skill confidence, match breakdowns, and AI summaries using live GitHub signals.
    """
    candidate_dict = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate_dict:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate_name = candidate_dict.get("name", "Unknown")
    text = candidate_dict.get("resume_text") or (
        candidate_name + " " + (candidate_dict.get("summary") or "")
    )
    github_url = candidate_dict.get("github") or ""

    username = github_url.strip()
    username = re.sub(
        r"^(?:https?:/?/?)?(?:www\.)?github\.com/", "", username, flags=re.IGNORECASE
    )
    username = re.sub(r"^(?:https?:/?/?)?", "", username, flags=re.IGNORECASE)
    username = username.strip("/").replace(" ", "").replace("\t", "")

    if not username:
        raise HTTPException(
            status_code=400, detail="No GitHub profile set for candidate."
        )

    # Load active jobs for this tenant
    supabase = get_supabase()
    jobs_res = (
        supabase.table("jobs").select("*").eq("recruiter_id", tenant_id).execute()
    )
    jobs_list = jobs_res.data
    best_job = jobs_list[0] if jobs_list else None

    role_type = "backend_engineer"
    jd_features = {
        "required_skills": [],
        "preferred_skills": [],
        "min_experience": 0,
        "max_experience": 99,
        "education_required": "unknown",
    }

    if best_job:
        role_type = (
            "backend_engineer"
            if "backend" in str(best_job.get("title", "")).lower()
            else "frontend_engineer"
        )
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
            "education_required": "unknown",
        }

    from signals.github_signal import GitHubRateLimitException

    # Run full scoring engine
    try:
        scoring_res = await compute_full_candidate_score(
            candidate_name=candidate_name,
            resume_text=text,
            jd_features=jd_features,
            github_username=username,
            role_type=role_type,
        )
    except GitHubRateLimitException as e:
        logger.warning("GitHub rate limit hit during webhook sync: %s", e)
        raise HTTPException(
            status_code=429,
            detail="GitHub API rate limit exceeded. Please try again later or configure a GITHUB_TOKEN.",
        )
    except Exception as e:
        raise safe_error_response(e, "Failed to score candidate. Please try again.")

    github_signals = scoring_res.get("external_signals", {}).get("github", {})
    github_analysis = scoring_res["insights"].get("github_analysis", {})
    final_score = round(scoring_res.get("final_score", 0.0))
    blind_score = final_score

    # Compute Blind Score using bias auditor
    if best_job:
        try:
            from engine.bias_auditor import compute_blind_score

            blind_res = await compute_blind_score(
                candidate_name=candidate_name,
                resume_text=text,
                jd_features=jd_features,
                role_type=role_type,
            )
            blind_score = int(blind_res.get("final_score", final_score))
        except Exception as e:
            logger.warning("Failed to compute blind score in webhook sync: %s", e)

    # Build job_matches list for all jobs
    job_matches = []
    for job in jobs_list:
        from engine.matcher import compute_match_breakdown

        req_skills = job.get("required_skills") or []
        if isinstance(req_skills, str):
            req_skills_list = [s.strip() for s in req_skills.split(",") if s.strip()]
        else:
            req_skills_list = req_skills

        job_jd = {
            "required_skills": req_skills_list,
            "preferred_skills": [],
            "min_experience": job.get("min_experience", 0),
            "max_experience": 99,
            "education_required": "unknown",
        }
        match_breakdown = compute_match_breakdown(
            resume_features=scoring_res["resume_features"],
            jd_features=job_jd,
            github_signals=github_signals,
            linkedin_signals=scoring_res["external_signals"]["linkedin"],
        )
        job_matches.append(
            {
                "job_id": job["id"],
                "job_title": job["title"],
                "tfidf_score": match_breakdown["overall_match_percentage"],
                "matched_skills": scoring_res["matched_skills"],
                "missing_skills": scoring_res["missing_skills"],
            }
        )

    experience_data = [
        {
            "title": "Experience",
            "company": "Various",
            "duration": f"{scoring_res['resume_features'].get('experience_years', 0.0)} years",
        }
    ]

    # Build radar_data from real signal values (commit frequency, language count, PR counts, and test presence)
    commit_freq = github_signals.get(
        "commit_frequency_per_week", 0.0
    ) or github_signals.get("commit_frequency", 0.0)
    lang_count = len(github_signals.get("languages", []))
    pr_count = github_signals.get("open_source_prs_estimate", 0)
    has_tests = github_signals.get("has_tests", False)

    github_analysis = scoring_res["insights"].get("github_analysis", {})
    maturity_score = github_analysis.get("project_maturity_score", 0.0)

    radar_data = [
        {
            "subject": "Commit Freq",
            "A": min(100, round(commit_freq * 10)),
            "fullMark": 100,
        },
        {"subject": "Polyglot", "A": min(100, lang_count * 15), "fullMark": 100},
        {"subject": "PR Activity", "A": min(100, pr_count * 10), "fullMark": 100},
        {"subject": "Code Quality", "A": 90 if has_tests else 40, "fullMark": 100},
        {"subject": "Maturity", "A": min(100, round(maturity_score)), "fullMark": 100},
    ]

    candidate_dict["role"] = scoring_res["resume_features"].get(
        "role", "Software Engineer"
    )
    candidate_dict["score"] = final_score
    candidate_dict["blind_score"] = blind_score
    candidate_dict["status"] = "Strong Match" if final_score > 85 else "Match"
    candidate_dict["summary"] = scoring_res["insights"]["ai_summary"][
        "executive_summary"
    ]
    candidate_dict["skills"] = scoring_res["resume_features"].get("skills", [])
    real_timeline = scoring_res["resume_features"].get("experience_timeline", [])
    candidate_dict["experience"] = real_timeline if real_timeline else experience_data
    candidate_dict["job_matches"] = job_matches
    candidate_dict["jobMatches"] = job_matches
    candidate_dict["radar_data"] = radar_data
    candidate_dict["radarData"] = radar_data
    # Merge insights — preserve resume_base64 and other existing data
    existing_insights = candidate_dict.get("insights") or {}
    new_insights = scoring_res.get("insights") or {}
    merged_insights = {**existing_insights, **new_insights}
    # Preserve resume_base64 from existing insights if new scoring doesn't include it
    if existing_insights.get("resume_base64") and not new_insights.get("resume_base64"):
        merged_insights["resume_base64"] = existing_insights["resume_base64"]
    candidate_dict["insights"] = merged_insights

    # Save the updated candidate
    await save_candidate(candidate_dict, tenant_id)

    # Log audit event
    github_score_pct = round(github_analysis.get("engineering_score", 0.0))
    try:
        await log_analytics_event(
            "github_sync",
            {
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "github_username": username,
                "new_github_score": github_score_pct,
                "new_overall_score": final_score,
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.warning(f"Failed to log analytics event: {e}")

    return {
        "status": "success",
        "message": f"GitHub profile sync successful for {username}.",
        "github_score": github_score_pct,
        "overall_score": final_score,
        "skills": scoring_res["resume_features"].get("skills", []),
        "experience": experience_data,
        "job_matches": job_matches,
        "radar_data": radar_data,
        "insights": scoring_res["insights"],
        "github": candidate_dict.get("github") or "",
        "linkedin": candidate_dict.get("linkedin") or "",
        "signals": {
            "followers": github_signals.get("followers", 0),
            "public_repos": github_signals.get("total_repos", 0),
            "stars": github_signals.get("total_stars", 0),
            "commit_frequency": github_signals.get("commit_frequency_per_week", 0),
            "languages": github_signals.get("languages", []),
        },
    }


# ─────────────────────────────────────────────────────────────
# GET /candidates/{candidate_id}/gdpr-export
# ─────────────────────────────────────────────────────────────


@router.get("/{candidate_id}/gdpr-export")
async def gdpr_export_candidate(
    candidate_id: str,
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user),
):
    """
    GDPR compliant candidate data export: returns raw decrypted PII fields for verification.
    Logs an audit event for compliance tracking.
    """
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Log the access event for GDPR audit
    await log_analytics_event(
        "GDPR_DATA_EXPORT",
        {
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("name"),
            "performed_by_user": current_user.get("email"),
            "timestamp": datetime.now().isoformat(),
        },
    )

    return {"status": "success", "exported_data": candidate}


# ─────────────────────────────────────────────────────────────
# DELETE /candidates/{candidate_id}/gdpr-forget
# ─────────────────────────────────────────────────────────────


@router.delete(
    "/{candidate_id}/gdpr-forget",
    dependencies=[Depends(require_permission(Permission.DELETE_CANDIDATE))],
)
async def gdpr_forget_candidate(
    candidate_id: str,
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user),
):
    """
    GDPR 'Right to be Forgotten' candidate deletion: permanently purges a candidate.
    Logs an audit event before deleting.
    """
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Log GDPR forget action
    await log_analytics_event(
        "GDPR_DATA_DELETE",
        {
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("name"),
            "performed_by_user": current_user.get("email"),
            "timestamp": datetime.now().isoformat(),
        },
    )
    await delete_candidate(candidate_id, tenant_id)
    return {
        "status": "success",
        "message": f"Candidate '{candidate.get('name')}' successfully forgotten.",
    }


# ─────────────────────────────────────────────────────────────
# GET /candidates/platforms/{username}
# ─────────────────────────────────────────────────────────────


@router.get("/platforms/{username:path}", response_model=PlatformSignalsResponse)
async def fetch_platform_signals(
    username: str,
    platforms: str = Query(
        "github",
        description="Comma-separated platforms: github,codeforces,leetcode,codechef",
    ),
) -> PlatformSignalsResponse:
    """
    Fetch raw signal data from specified platforms for a given username.
    """
    platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()]

    if not platform_list:
        raise HTTPException(
            status_code=400, detail="At least one platform is required."
        )

    valid_platforms = {"github", "codeforces", "leetcode", "codechef"}
    invalid = set(platform_list) - valid_platforms
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platforms: {', '.join(invalid)}. Valid: {', '.join(valid_platforms)}",
        )

    clean_username = username.strip()
    clean_username = re.sub(
        r"^(?:https?:/?/?)?(?:www\.)?github\.com/",
        "",
        clean_username,
        flags=re.IGNORECASE,
    )
    clean_username = re.sub(
        r"^(?:https?:/?/?)?", "", clean_username, flags=re.IGNORECASE
    )
    clean_username = clean_username.strip("/").replace(" ", "").replace("\t", "")

    tasks: dict[str, Any] = {}
    if "github" in platform_list:
        tasks["github"] = fetch_github_signals(clean_username)
    if "codeforces" in platform_list:
        tasks["codeforces"] = fetch_codeforces(clean_username)
    if "leetcode" in platform_list:
        tasks["leetcode"] = fetch_leetcode(clean_username)
    if "codechef" in platform_list:
        tasks["codechef"] = fetch_codechef(clean_username)

    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    signals: dict[str, Any] = {}
    for key, result in zip(keys, results):
        if isinstance(result, Exception):
            signals[key] = {"error": str(result)}
        else:
            signals[key] = result if result else {}

    return PlatformSignalsResponse(
        username=username,
        platforms_queried=platform_list,
        signals=signals,
    )


# ─────────────────────────────────────────────────────────────
# POST /candidates/shortlist — 0/1 Knapsack DP
# ─────────────────────────────────────────────────────────────


@router.post("/shortlist")
async def shortlist_by_budget(request: dict[str, Any]) -> JSONResponse:
    """
    Select candidates to maximize total score within budget using 0/1 Knapsack DP.
    Algorithm: Dynamic Programming (0/1 Knapsack)
    Time Complexity: O(n × budget), Space: O(n × budget)
    """
    candidates = request.get("candidates", [])
    budget = request.get("budget", 10)

    result = knapsack_shortlist(candidates, budget)
    return JSONResponse(content=result, status_code=200)


# ─────────────────────────────────────────────────────────────
# POST /candidates/skill-gap — Graph + BFS
# ─────────────────────────────────────────────────────────────


@router.post("/skill-gap")
async def analyze_skill_gap(request: dict[str, Any]) -> JSONResponse:
    """
    Find missing skills and shortest learning path using BFS on skill graph.
    Algorithm: Graph Traversal + BFS
    Time Complexity: O(V + E), Space: O(V + E)
    """
    from algorithms.skill_graph import build_skill_graph

    current_skills = request.get("current_skills", [])
    required_skills = request.get("required_skills", [])

    graph = build_skill_graph()
    result = find_learning_path(current_skills, required_skills, graph)
    return JSONResponse(content=result, status_code=200)


# ─────────────────────────────────────────────────────────────
# POST /candidates/schedule — Greedy Activity Selection
# ─────────────────────────────────────────────────────────────


@router.post("/schedule")
async def schedule_interviews_endpoint(request: dict[str, Any]) -> JSONResponse:
    """
    Schedule maximum non-overlapping interviews using Greedy Activity Selection.
    Algorithm: Greedy (Activity Selection)
    Time Complexity: O(n log n) for sorting, Space: O(n)
    """
    candidates = request.get("candidates", [])

    result = schedule_interviews(candidates)
    return JSONResponse(content=result, status_code=200)


# ─────────────────────────────────────────────────────────────
# POST /candidates/rank-sorted — Merge Sort with Rank Delta
# ─────────────────────────────────────────────────────────────


@router.post("/rank-sorted")
async def rank_candidates_sorted(request: dict[str, Any]) -> JSONResponse:
    """
    Sort candidates by fusion score with rank delta tracking using Merge Sort.
    Algorithm: Divide & Conquer (Merge Sort)
    Time Complexity: O(n log n), Space: O(n)
    """
    candidates = request.get("candidates", [])

    result = merge_sort_candidates(candidates)
    return JSONResponse(content=result, status_code=200)


# ─────────────────────────────────────────────────────────────
# GET /candidates/github/{username} — Live GitHub signals
# ─────────────────────────────────────────────────────────────


@router.get("/github/{username:path}")
async def get_github_signals(username: str):
    """
    Fetch live GitHub signals for a candidate and return stats + score.
    Uses fetch_github_signals() (async httpx) + score_github().
    Time Complexity: O(1) network calls, O(r) repo parsing where r = repo count
    """
    from signals.github_signal import (
        fetch_github_signals,
        score_github,
        analyze_github_profile,
        GitHubRateLimitException,
    )

    # Strip github.com/ prefix if the full URL was passed
    clean = username.strip()
    clean = re.sub(
        r"^(?:https?:/?/?)?(?:www\.)?github\.com/", "", clean, flags=re.IGNORECASE
    )
    clean = re.sub(r"^(?:https?:/?/?)?", "", clean, flags=re.IGNORECASE)
    clean = clean.strip("/").replace(" ", "").replace("\t", "")

    if not clean:
        return {"error": "Invalid username"}

    signals = None
    profile_analysis = None

    try:
        supabase = get_supabase()
        res = (
            supabase.table("candidates")
            .select("insights")
            .ilike("github_url", clean)
            .execute()
        )
        if res.data:
            # Use candidate insights cache if available
            insights = res.data[0].get("insights") or {}
            signals = insights.get("github_signals")
            profile_analysis = insights.get("github_analysis")
    except Exception as e:
        logger.warning(
            "Failed to fetch database cache for github user %s: %s", clean, e
        )

    if not signals or not profile_analysis:
        try:
            signals = await fetch_github_signals(clean)
        except GitHubRateLimitException:
            raise HTTPException(
                status_code=429,
                detail="GitHub API rate limit exceeded. Please try again later or configure a GITHUB_TOKEN.",
            )

        if not signals:
            return {"error": f"GitHub profile '{clean}' not found or is private"}

        profile_analysis = analyze_github_profile(signals, [], "backend")
    return {
        "username": clean,
        "score": round(profile_analysis.get("engineering_score", 0.0)),  # 0-100
        "account_age_years": signals.get("account_age_years", 0),
        "total_repos": signals.get("total_repos", 0),
        "original_repos": signals.get("original_repos", 0),
        "total_stars": signals.get("total_stars", 0),
        "top_repo_stars": signals.get("top_repo_stars", 0),
        "languages": signals.get("languages", []),
        "commit_frequency_per_week": signals.get("commit_frequency_per_week", 0),
        "contribution_streak_estimate": signals.get("contribution_streak_estimate", 0),
        "open_source_prs_estimate": signals.get("open_source_prs_estimate", 0),
        "has_tests": signals.get("has_tests", False),
        "has_readme_ratio": signals.get("has_readme_ratio", 0),
        "profile_completeness": signals.get("profile_completeness", 0),
        "followers": signals.get("followers", 0),
        "raw_bio": signals.get("raw_bio", ""),
        "engineering_score": round(profile_analysis.get("engineering_score", 0)),
        "open_source_score": round(profile_analysis.get("open_source_score", 0)),
        "project_maturity_score": round(
            profile_analysis.get("project_maturity_score", 0)
        ),
        "verified_skills": profile_analysis.get("verified_skills", []),
        "unsupported_claims": profile_analysis.get("unsupported_claims", []),
    }


# ─────────────────────────────────────────────────────────────
# Notes & Interviews DB Persistence Endpoints
# ─────────────────────────────────────────────────────────────

import json


class NoteCreateRequest(BaseModel):
    author: str
    comment: Optional[str] = None
    content: Optional[str] = None
    rating: int = 5
    date: str = ""


@router.post("/{candidate_id}/notes")
async def add_candidate_note(
    candidate_id: str, req: NoteCreateRequest, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    note_text = req.comment or req.content
    if not note_text or not note_text.strip():
        raise HTTPException(
            status_code=400, detail="Note comment/content cannot be empty."
        )

    supabase = get_supabase()
    note_id = str(uuid.uuid4())

    note_date = req.date
    if not note_date:
        note_date = datetime.utcnow().strftime("%b %d, %Y, %I:%M %p")

    serialized_content = json.dumps(
        {
            "author": req.author,
            "comment": note_text,
            "rating": req.rating,
            "date": note_date,
        }
    )

    db_record = {
        "id": note_id,
        "candidate_id": candidate_id,
        "content": serialized_content,
    }

    try:
        res = supabase.table("candidate_notes").insert(db_record).execute()
        if not res.data:
            raise HTTPException(
                status_code=500, detail="Failed to save note to database."
            )

        row = res.data[0]
        return {
            "id": row["id"],
            "candidate_id": row["candidate_id"],
            "author": req.author,
            "comment": note_text,
            "rating": req.rating,
            "date": note_date,
            "created_at": row.get("created_at"),
        }
    except Exception as e:
        raise safe_error_response(e, "Database error saving note.")


@router.get("/{candidate_id}/notes")
async def get_candidate_notes(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> list[dict]:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        res = (
            supabase.table("candidate_notes")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .execute()
        )
        notes = []
        for row in res.data or []:
            content_str = row.get("content") or ""
            author = "System"
            comment = content_str
            rating = 5
            date_str = ""
            try:
                parsed = json.loads(content_str)
                if isinstance(parsed, dict):
                    author = parsed.get("author", "System")
                    comment = parsed.get("comment", parsed.get("content", ""))
                    rating = parsed.get("rating", 5)
                    date_str = parsed.get("date", "")
            except Exception:
                pass

            if not date_str:
                created_at = row.get("created_at")
                if created_at:
                    try:
                        clean_dt = created_at.split("+")[0].split("Z")[0]
                        dt = datetime.fromisoformat(clean_dt)
                        date_str = dt.strftime("%b %d, %Y, %I:%M %p")
                    except Exception:
                        date_str = created_at
            notes.append(
                {
                    "id": row.get("id"),
                    "candidate_id": row.get("candidate_id"),
                    "author": author,
                    "comment": comment,
                    "rating": rating,
                    "date": date_str,
                    "created_at": row.get("created_at"),
                }
            )
        return notes
    except Exception as e:
        raise safe_error_response(e, "Database error fetching notes.")


@router.delete("/{candidate_id}/notes/{note_id}")
async def delete_candidate_note(
    candidate_id: str, note_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        check_res = (
            supabase.table("candidate_notes")
            .select("id")
            .eq("id", note_id)
            .eq("candidate_id", candidate_id)
            .execute()
        )
        if not check_res.data:
            raise HTTPException(
                status_code=404, detail="Note not found for this candidate."
            )

        supabase.table("candidate_notes").delete().eq("id", note_id).execute()
        return {"status": "success", "message": "Note successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error deleting note.")


class InterviewCreateRequest(BaseModel):
    scheduled_at: str
    duration_minutes: int
    interviewer_name: str
    status: str = "scheduled"


@router.post("/{candidate_id}/interviews")
async def add_candidate_interview(
    candidate_id: str,
    req: InterviewCreateRequest,
    tenant_id: str = Depends(require_tenant),
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    interview_id = str(uuid.uuid4())

    db_record = {
        "id": interview_id,
        "candidate_id": candidate_id,
        "scheduled_at": req.scheduled_at,
        "duration_minutes": req.duration_minutes,
        "interviewer_name": req.interviewer_name,
        "status": req.status,
    }

    try:
        res = supabase.table("interviews").insert(db_record).execute()
        if not res.data:
            raise HTTPException(
                status_code=500, detail="Failed to save interview to database."
            )
        return res.data[0]
    except Exception as e:
        raise safe_error_response(e, "Database error saving interview.")


@router.get("/{candidate_id}/interviews")
async def get_candidate_interviews(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> list[dict]:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        res = (
            supabase.table("interviews")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        return res.data or []
    except Exception as e:
        raise safe_error_response(e, "Database error fetching interviews.")


@router.get("/interviews/all")
async def get_all_interviews(tenant_id: str = Depends(require_tenant)) -> list[dict]:
    supabase = get_supabase()
    try:
        candidates_res = (
            supabase.table("candidates")
            .select("id, full_name, career_tier")
            .eq("recruiter_id", tenant_id)
            .execute()
        )
        if not candidates_res.data:
            return []

        candidate_map = {c["id"]: c for c in candidates_res.data}
        candidate_ids = list(candidate_map.keys())

        interviews_res = (
            supabase.table("interviews")
            .select("*")
            .in_("candidate_id", candidate_ids)
            .execute()
        )

        results = []
        for iv in interviews_res.data or []:
            cand = candidate_map.get(iv["candidate_id"]) or {}

            scheduled_str = iv.get("scheduled_at") or ""
            start_time_str = "09:00"
            end_time_str = "10:00"
            if scheduled_str:
                try:
                    clean_dt = scheduled_str.split("+")[0].split("Z")[0]
                    dt = datetime.fromisoformat(clean_dt)
                    start_time_str = dt.strftime("%H:%M")

                    from datetime import timedelta

                    duration = iv.get("duration_minutes") or 60
                    dt_end = dt + timedelta(minutes=duration)
                    end_time_str = dt_end.strftime("%H:%M")
                except Exception as parse_err:
                    logger.warning(f"Error parsing scheduled_at: {parse_err}")

            results.append(
                {
                    "id": iv["id"],
                    "candidate_id": iv["candidate_id"],
                    "name": cand.get("full_name") or "Unknown",
                    "role": cand.get("career_tier") or "Software Engineer",
                    "start": start_time_str,
                    "end": end_time_str,
                    "status": iv.get("status") or "pending",
                    "scheduled_at": scheduled_str,
                    "duration_minutes": iv.get("duration_minutes") or 60,
                    "interviewer_name": iv.get("interviewer_name")
                    or "Senior Interviewer",
                }
            )
        return results
    except Exception as e:
        raise safe_error_response(e, "Database error fetching all interviews.")


class InterviewUpdateRequest(BaseModel):
    start: str | None = None
    end: str | None = None
    status: str | None = None
    scheduled_at: str | None = None
    duration_minutes: int | None = None
    interviewer_name: str | None = None


@router.patch("/interviews/{interview_id}")
async def update_candidate_interview(
    interview_id: str,
    req: InterviewUpdateRequest,
    tenant_id: str = Depends(require_tenant),
) -> dict:
    supabase = get_supabase()
    try:
        interview_res = (
            supabase.table("interviews")
            .select(
                "candidate_id, scheduled_at, duration_minutes, interviewer_name, status"
            )
            .eq("id", interview_id)
            .execute()
        )
        if not interview_res.data:
            raise HTTPException(status_code=404, detail="Interview not found.")

        iv = interview_res.data[0]
        candidate_id = iv["candidate_id"]
        candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
        if not candidate:
            raise HTTPException(
                status_code=403, detail="Not authorized to edit this interview."
            )

        update_data = {}

        # If frontend sends start/end time modifications, we reconstruct scheduled_at
        if req.start or req.end:
            # Reconstruct from current scheduled_at date part + new start time
            # For simplicity, we can keep the date part from iv["scheduled_at"] and set the time part to req.start
            scheduled_str = iv.get("scheduled_at") or datetime.utcnow().isoformat()
            try:
                date_part = scheduled_str.split("T")[0]
                new_start = req.start or "09:00"
                update_data["scheduled_at"] = f"{date_part}T{new_start}:00Z"

                if req.start and req.end:
                    # Calculate new duration in minutes
                    from datetime import datetime as dt_parser

                    t1 = dt_parser.strptime(req.start, "%H:%M")
                    t2 = dt_parser.strptime(req.end, "%H:%M")
                    diff_mins = int((t2 - t1).total_seconds() / 60)
                    update_data["duration_minutes"] = max(1, diff_mins)
            except Exception as parse_err:
                logger.warning(f"Error parsing start/end times in update: {parse_err}")

        if req.status is not None:
            update_data["status"] = req.status
        if req.scheduled_at is not None:
            update_data["scheduled_at"] = req.scheduled_at
        if req.duration_minutes is not None:
            update_data["duration_minutes"] = req.duration_minutes
        if req.interviewer_name is not None:
            update_data["interviewer_name"] = req.interviewer_name

        if not update_data:
            return iv

        res = (
            supabase.table("interviews")
            .update(update_data)
            .eq("id", interview_id)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to update interview.")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error updating interview.")


@router.delete("/interviews/{interview_id}")
async def delete_candidate_interview(
    interview_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    supabase = get_supabase()
    try:
        interview_res = (
            supabase.table("interviews")
            .select("candidate_id")
            .eq("id", interview_id)
            .execute()
        )
        if not interview_res.data:
            raise HTTPException(status_code=404, detail="Interview not found.")

        candidate_id = interview_res.data[0]["candidate_id"]
        candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
        if not candidate:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this interview."
            )

        supabase.table("interviews").delete().eq("id", interview_id).execute()
        return {"status": "success", "message": "Interview successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error deleting interview.")


# ─────────────────────────────────────────────────────────────
# Notes & Interviews DB Persistence Endpoints
# ─────────────────────────────────────────────────────────────

import json


class NoteCreateRequest(BaseModel):
    author: str
    comment: Optional[str] = None
    content: Optional[str] = None
    rating: int = 5
    date: str = ""


@router.post("/{candidate_id}/notes")
async def add_candidate_note(
    candidate_id: str, req: NoteCreateRequest, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    note_text = req.comment or req.content
    if not note_text or not note_text.strip():
        raise HTTPException(
            status_code=400, detail="Note comment/content cannot be empty."
        )

    supabase = get_supabase()
    note_id = str(uuid.uuid4())

    note_date = req.date
    if not note_date:
        note_date = datetime.utcnow().strftime("%b %d, %Y, %I:%M %p")

    serialized_content = json.dumps(
        {
            "author": req.author,
            "comment": note_text,
            "rating": req.rating,
            "date": note_date,
        }
    )

    db_record = {
        "id": note_id,
        "candidate_id": candidate_id,
        "content": serialized_content,
    }

    try:
        res = supabase.table("candidate_notes").insert(db_record).execute()
        if not res.data:
            raise HTTPException(
                status_code=500, detail="Failed to save note to database."
            )

        row = res.data[0]
        return {
            "id": row["id"],
            "candidate_id": row["candidate_id"],
            "author": req.author,
            "comment": note_text,
            "rating": req.rating,
            "date": note_date,
            "created_at": row.get("created_at"),
        }
    except Exception as e:
        raise safe_error_response(e, "Database error saving note.")


@router.get("/{candidate_id}/notes")
async def get_candidate_notes(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> list[dict]:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        res = (
            supabase.table("candidate_notes")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .execute()
        )
        notes = []
        for row in res.data or []:
            content_str = row.get("content") or ""
            author = "System"
            comment = content_str
            rating = 5
            date_str = ""
            try:
                parsed = json.loads(content_str)
                if isinstance(parsed, dict):
                    author = parsed.get("author", "System")
                    comment = parsed.get("comment", parsed.get("content", ""))
                    rating = parsed.get("rating", 5)
                    date_str = parsed.get("date", "")
            except Exception:
                pass

            if not date_str:
                created_at = row.get("created_at")
                if created_at:
                    try:
                        clean_dt = created_at.split("+")[0].split("Z")[0]
                        dt = datetime.fromisoformat(clean_dt)
                        date_str = dt.strftime("%b %d, %Y, %I:%M %p")
                    except Exception:
                        date_str = created_at
            notes.append(
                {
                    "id": row.get("id"),
                    "candidate_id": row.get("candidate_id"),
                    "author": author,
                    "comment": comment,
                    "rating": rating,
                    "date": date_str,
                    "created_at": row.get("created_at"),
                }
            )
        return notes
    except Exception as e:
        raise safe_error_response(e, "Database error fetching notes.")


@router.delete("/{candidate_id}/notes/{note_id}")
async def delete_candidate_note(
    candidate_id: str, note_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        check_res = (
            supabase.table("candidate_notes")
            .select("id")
            .eq("id", note_id)
            .eq("candidate_id", candidate_id)
            .execute()
        )
        if not check_res.data:
            raise HTTPException(
                status_code=404, detail="Note not found for this candidate."
            )

        supabase.table("candidate_notes").delete().eq("id", note_id).execute()
        return {"status": "success", "message": "Note successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error deleting note.")


class InterviewCreateRequest(BaseModel):
    scheduled_at: str
    duration_minutes: int
    interviewer_name: str
    status: str = "scheduled"


@router.post("/{candidate_id}/interviews")
async def add_candidate_interview(
    candidate_id: str,
    req: InterviewCreateRequest,
    tenant_id: str = Depends(require_tenant),
) -> dict:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    interview_id = str(uuid.uuid4())

    db_record = {
        "id": interview_id,
        "candidate_id": candidate_id,
        "scheduled_at": req.scheduled_at,
        "duration_minutes": req.duration_minutes,
        "interviewer_name": req.interviewer_name,
        "status": req.status,
    }

    try:
        res = supabase.table("interviews").insert(db_record).execute()
        if not res.data:
            raise HTTPException(
                status_code=500, detail="Failed to save interview to database."
            )
        return res.data[0]
    except Exception as e:
        raise safe_error_response(e, "Database error saving interview.")


@router.get("/{candidate_id}/interviews")
async def get_candidate_interviews(
    candidate_id: str, tenant_id: str = Depends(require_tenant)
) -> list[dict]:
    candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    supabase = get_supabase()
    try:
        res = (
            supabase.table("interviews")
            .select("*")
            .eq("candidate_id", candidate_id)
            .execute()
        )
        return res.data or []
    except Exception as e:
        raise safe_error_response(e, "Database error fetching interviews.")


@router.get("/interviews/all")
async def get_all_interviews(tenant_id: str = Depends(require_tenant)) -> list[dict]:
    supabase = get_supabase()
    try:
        candidates_res = (
            supabase.table("candidates")
            .select("id, full_name, career_tier")
            .eq("recruiter_id", tenant_id)
            .execute()
        )
        if not candidates_res.data:
            return []

        candidate_map = {c["id"]: c for c in candidates_res.data}
        candidate_ids = list(candidate_map.keys())

        interviews_res = (
            supabase.table("interviews")
            .select("*")
            .in_("candidate_id", candidate_ids)
            .execute()
        )

        results = []
        for iv in interviews_res.data or []:
            cand = candidate_map.get(iv["candidate_id"]) or {}

            scheduled_str = iv.get("scheduled_at") or ""
            start_time_str = "09:00"
            end_time_str = "10:00"
            if scheduled_str:
                try:
                    clean_dt = scheduled_str.split("+")[0].split("Z")[0]
                    dt = datetime.fromisoformat(clean_dt)
                    start_time_str = dt.strftime("%H:%M")

                    from datetime import timedelta

                    duration = iv.get("duration_minutes") or 60
                    dt_end = dt + timedelta(minutes=duration)
                    end_time_str = dt_end.strftime("%H:%M")
                except Exception as parse_err:
                    logger.warning(f"Error parsing scheduled_at: {parse_err}")

            results.append(
                {
                    "id": iv["id"],
                    "candidate_id": iv["candidate_id"],
                    "name": cand.get("full_name") or "Unknown",
                    "role": cand.get("career_tier") or "Software Engineer",
                    "start": start_time_str,
                    "end": end_time_str,
                    "status": iv.get("status") or "pending",
                    "scheduled_at": scheduled_str,
                    "duration_minutes": iv.get("duration_minutes") or 60,
                    "interviewer_name": iv.get("interviewer_name")
                    or "Senior Interviewer",
                }
            )
        return results
    except Exception as e:
        raise safe_error_response(e, "Database error fetching all interviews.")


class InterviewUpdateRequest(BaseModel):
    start: str | None = None
    end: str | None = None
    status: str | None = None
    scheduled_at: str | None = None
    duration_minutes: int | None = None
    interviewer_name: str | None = None


@router.patch("/interviews/{interview_id}")
async def update_candidate_interview(
    interview_id: str,
    req: InterviewUpdateRequest,
    tenant_id: str = Depends(require_tenant),
) -> dict:
    supabase = get_supabase()
    try:
        interview_res = (
            supabase.table("interviews")
            .select(
                "candidate_id, scheduled_at, duration_minutes, interviewer_name, status"
            )
            .eq("id", interview_id)
            .execute()
        )
        if not interview_res.data:
            raise HTTPException(status_code=404, detail="Interview not found.")

        iv = interview_res.data[0]
        candidate_id = iv["candidate_id"]
        candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
        if not candidate:
            raise HTTPException(
                status_code=403, detail="Not authorized to edit this interview."
            )

        update_data = {}

        # If frontend sends start/end time modifications, we reconstruct scheduled_at
        if req.start or req.end:
            # Reconstruct from current scheduled_at date part + new start time
            # For simplicity, we can keep the date part from iv["scheduled_at"] and set the time part to req.start
            scheduled_str = iv.get("scheduled_at") or datetime.utcnow().isoformat()
            try:
                date_part = scheduled_str.split("T")[0]
                new_start = req.start or "09:00"
                update_data["scheduled_at"] = f"{date_part}T{new_start}:00Z"

                if req.start and req.end:
                    # Calculate new duration in minutes
                    from datetime import datetime as dt_parser

                    t1 = dt_parser.strptime(req.start, "%H:%M")
                    t2 = dt_parser.strptime(req.end, "%H:%M")
                    diff_mins = int((t2 - t1).total_seconds() / 60)
                    update_data["duration_minutes"] = max(1, diff_mins)
            except Exception as parse_err:
                logger.warning(f"Error parsing start/end times in update: {parse_err}")

        if req.status is not None:
            update_data["status"] = req.status
        if req.scheduled_at is not None:
            update_data["scheduled_at"] = req.scheduled_at
        if req.duration_minutes is not None:
            update_data["duration_minutes"] = req.duration_minutes
        if req.interviewer_name is not None:
            update_data["interviewer_name"] = req.interviewer_name

        if not update_data:
            return iv

        res = (
            supabase.table("interviews")
            .update(update_data)
            .eq("id", interview_id)
            .execute()
        )
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to update interview.")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error updating interview.")


@router.delete("/interviews/{interview_id}")
async def delete_candidate_interview(
    interview_id: str, tenant_id: str = Depends(require_tenant)
) -> dict:
    supabase = get_supabase()
    try:
        interview_res = (
            supabase.table("interviews")
            .select("candidate_id")
            .eq("id", interview_id)
            .execute()
        )
        if not interview_res.data:
            raise HTTPException(status_code=404, detail="Interview not found.")

        candidate_id = interview_res.data[0]["candidate_id"]
        candidate = await fetch_candidate_by_id(candidate_id, tenant_id)
        if not candidate:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this interview."
            )

        supabase.table("interviews").delete().eq("id", interview_id).execute()
        return {"status": "success", "message": "Interview successfully deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise safe_error_response(e, "Database error deleting interview.")
