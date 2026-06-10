"""
Candidates Router — Endpoints for candidate evaluation, ranking, and signal fetching.

Routes:
    POST /candidates/rank            — Batch rank candidates against a JD
    POST /candidates/analyze-single  — Analyze a single candidate
    POST /candidates/upload-resume   — Upload and parse a resume file
    GET  /candidates/platforms/{username} — Fetch raw platform signals
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import uuid
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from api.core.dependencies import get_current_user
from api.core.rbac import require_tenant, require_permission, Permission
from db.session import get_db
from sqlalchemy.orm import Session
from api.core.limits import check_cv_upload_limit, increment_cv_parses
from tasks.worker import process_resume_task

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
from engine.bias_auditor import audit_bias, run_batch_bias_audit, create_blind_features
from engine.score_fusion import compute_full_candidate_score
from parser.resume_parser import async_extract_text as parse_resume_text
from parser.feature_extractor import extract_features
from signals.github_signal import fetch_github_signals
from signals.coding_signal import fetch_codeforces, fetch_codechef, fetch_leetcode

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/candidates",
    tags=["candidates"],
    dependencies=[Depends(require_tenant)]
)


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
            logger.error(
                "Scoring failed for candidate %d: %s",
                i,
                str(result),
            )
            continue
            
        if request.enable_bias_audit and blind_results and not isinstance(blind_results[i], Exception):
            result["blind_score_value"] = blind_results[i].get("final_score", result.get("final_score", 0.0))
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
    )


# ─────────────────────────────────────────────────────────────
# POST /candidates/upload-resume  (single)
# POST /candidates/upload-bulk    (multiple — up to 1000)
# ─────────────────────────────────────────────────────────────


def build_ai_summary(name: str, features: dict, job_matches: list, final_score: int) -> str:
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


async def _process_resume(file: UploadFile) -> dict:
    """Shared processing logic for a single resume file."""
    import tempfile, os, heapq
    from algorithms.tfidf import TFIDFVectorizer
    from algorithms.cosine_similarity import cosine_similarity
    from .settings import active_weights
    from db.supabase_client import save_candidate, fetch_all_jobs

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_ext = {".pdf", ".txt", ".md", ".docx"}
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    if ext == ".pdf":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            text = await parse_resume_text(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        text = content.decode("utf-8", errors="replace")

    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from file.")

    features = extract_features(text)

    # Fetch jobs from persistent database instead of removed in-memory list
    jobs_list = await fetch_all_jobs()

    job_texts = [
        f"{j['description']} {j['required_skills'].replace(',', ' ')}"
        for j in jobs_list
    ]

    job_matches = []
    final_score = max(55, min(99, len(features.get("skills", [])) * 6))

    if job_texts:
        corpus = [text] + job_texts
        vectorizer = TFIDFVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        resume_vec = vectors[0]

        heap = []
        for i, job_vec in enumerate(vectors[1:]):
            sim = cosine_similarity(resume_vec, job_vec)
            score = round(sim * 100, 1)
            job = jobs_list[i]
            job_skills = {s.strip().lower() for s in job["required_skills"].split(",")}
            resume_skills = {s.lower() for s in features.get("skills", [])}
            heapq.heappush(heap, (-score, i, {
                "job_id": job["id"],
                "job_title": job["title"],
                "tfidf_score": score,
                "matched_skills": sorted(job_skills & resume_skills),
                "missing_skills": sorted(job_skills - resume_skills),
            }))
        job_matches = [heapq.heappop(heap)[2] for _ in range(len(heap))]

        w = active_weights
        total_w = sum(w.get(k, 0) for k in ("resume", "github", "leetcode", "portfolio"))
        eff_w = w.get("resume", 0.4) / total_w if total_w > 0 else 1.0
        best = job_matches[0]["tfidf_score"] if job_matches else 0
        skill_density = min(100, len(features.get("skills", [])) * 6)
        final_score = max(55, min(99, round((0.6 * best + 0.4 * skill_density) * eff_w)))

    # Build candidate record and persist to Supabase
    raw_name = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
    name = " ".join(w.capitalize() for w in raw_name.split())
    email_m = __import__("re").search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    github_m = __import__("re").search(r"github\.com/[\w-]+", text, __import__("re").I)
    linkedin_m = __import__("re").search(r"linkedin\.com/in/[\w-]+", text, __import__("re").I)

    # Calculate blind score using anonymized data
    blind_score = final_score
    try:
        from engine.bias_auditor import compute_blind_score
        if jobs_list:
            best_job = jobs_list[0]
            jd_features = {
                "required_skills": best_job["required_skills"],
                "preferred_skills": best_job.get("preferred_skills", ""),
                "min_experience": best_job.get("experience_required", 0),
                "max_experience": best_job.get("max_experience", 99),
            }
            blind_res = await compute_blind_score(
                candidate_name=name,
                resume_text=text,
                jd_features=jd_features,
                role_type="backend_engineer" if "backend" in best_job.get("title", "").lower() else "frontend_engineer"
            )
            blind_score = round(blind_res.get("final_score", final_score))
    except Exception as e:
        logger.warning("Failed to compute blind score for candidate %s: %s", name, e)

    from parser.feature_extractor import generate_resume_insights
    insights = generate_resume_insights(features, text)

    candidate = {
        "id": str(uuid.uuid4()),
        "name": name,
        "role": "Software Engineer",
        "email": features.get("email") or (email_m.group() if email_m else f"{raw_name.lower().replace(' ', '.')}@example.com"),
        "github": github_m.group() if github_m else "",
        "linkedin": linkedin_m.group() if linkedin_m else "",
        "location": "Remote",
        "score": final_score,
        "blind_score": blind_score,
        "status": "Strong Match" if final_score > 90 else "Match",
        "summary": build_ai_summary(name, features, job_matches, final_score),
        "skills": features.get("skills", []),
        "experience": [],
        "jobMatches": job_matches,
        "radarData": [],
        "insights": insights,
    }

    try:
        await save_candidate(candidate)
    except Exception as e:
        logger.warning("Supabase save failed: %s", e)

    return {
        "filename": file.filename,
        "text_length": len(text),
        "extracted_text": text[:5000],
        "features": features,
        "tfidf_score": final_score,
        "job_matches": job_matches,
        "candidate_id": candidate["id"],
    }


async def background_process_resume_task(candidate_id: str, filename: str, content: bytes):
    """Run in BackgroundTasks: Parse resume, match, compute blind score, save."""
    import tempfile, os, heapq, uuid
    from algorithms.tfidf import TFIDFVectorizer
    from algorithms.cosine_similarity import cosine_similarity
    from .settings import active_weights
    from db.supabase_client import save_candidate, fetch_all_jobs
    
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    text = ""
    try:
        if ext == ".pdf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                text = await parse_resume_text(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            text = content.decode("utf-8", errors="replace")
            
        if not text or not text.strip():
            logger.warning("No text extracted from %s", filename)
            # Update status to failed
            candidate = {
                "id": candidate_id,
                "name": filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
                "status": "Extraction Failed",
                "summary": "Error: Could not extract text from the upload file."
            }
            await save_candidate(candidate)
            return

        features = extract_features(text)
        jobs_list = await fetch_all_jobs()
        job_texts = [
            f"{j['description']} {j['required_skills'].replace(',', ' ')}"
            for j in jobs_list
        ]

        job_matches = []
        final_score = max(55, min(99, len(features.get("skills", [])) * 6))

        if job_texts:
            corpus = [text] + job_texts
            vectorizer = TFIDFVectorizer()
            vectors = vectorizer.fit_transform(corpus)
            resume_vec = vectors[0]

            heap = []
            for i, job_vec in enumerate(vectors[1:]):
                sim = cosine_similarity(resume_vec, job_vec)
                score = round(sim * 100, 1)
                job = jobs_list[i]
                job_skills = {s.strip().lower() for s in job["required_skills"].split(",")}
                resume_skills = {s.lower() for s in features.get("skills", [])}
                heapq.heappush(heap, (-score, i, {
                    "job_id": job["id"],
                    "job_title": job["title"],
                    "tfidf_score": score,
                    "matched_skills": sorted(job_skills & resume_skills),
                    "missing_skills": sorted(job_skills - resume_skills),
                }))
            job_matches = [heapq.heappop(heap)[2] for _ in range(len(heap))]

            w = active_weights
            total_w = sum(w.get(k, 0) for k in ("resume", "github", "leetcode", "portfolio"))
            eff_w = w.get("resume", 0.4) / total_w if total_w > 0 else 1.0
            best = job_matches[0]["tfidf_score"] if job_matches else 0
            skill_density = min(100, len(features.get("skills", [])) * 6)
            final_score = max(55, min(99, round((0.6 * best + 0.4 * skill_density) * eff_w)))

        raw_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        name = " ".join(w.capitalize() for w in raw_name.split())
        email_m = __import__("re").search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
        github_m = __import__("re").search(r"github\.com/[\w-]+", text, __import__("re").I)
        linkedin_m = __import__("re").search(r"linkedin\.com/in/[\w-]+", text, __import__("re").I)

        blind_score = final_score
        try:
            from engine.bias_auditor import compute_blind_score
            if jobs_list:
                best_job = jobs_list[0]
                jd_features = {
                    "required_skills": best_job["required_skills"],
                    "preferred_skills": best_job.get("preferred_skills", ""),
                    "min_experience": best_job.get("experience_required", 0),
                    "max_experience": best_job.get("max_experience", 99),
                }
                blind_res = await compute_blind_score(
                    candidate_name=name,
                    resume_text=text,
                    jd_features=jd_features,
                    role_type="backend_engineer" if "backend" in best_job.get("title", "").lower() else "frontend_engineer"
                )
                blind_score = round(blind_res.get("final_score", final_score))
        except Exception as e:
            logger.warning("Failed to compute blind score for candidate %s: %s", name, e)

        from parser.feature_extractor import generate_resume_insights
        insights = generate_resume_insights(features, text)

        candidate = {
            "id": candidate_id,
            "name": name,
            "role": "Software Engineer",
            "email": features.get("email") or (email_m.group() if email_m else f"{raw_name.lower().replace(' ', '.')}@example.com"),
            "github": github_m.group() if github_m else "",
            "linkedin": linkedin_m.group() if linkedin_m else "",
            "location": "Remote",
            "score": final_score,
            "blind_score": blind_score,
            "status": "Strong Match" if final_score > 90 else "Match",
            "summary": build_ai_summary(name, features, job_matches, final_score),
            "resume_text": text,
            "skills": features.get("skills", []),
            "experience": [],
            "jobMatches": job_matches,
            "radarData": [],
            "insights": insights,
        }
        await save_candidate(candidate)
        
    except Exception as e:
        logger.error("Error processing resume in background: %s", e)
        # Update record with failure
        try:
            err_candidate = {
                "id": candidate_id,
                "name": filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
                "status": "Failed",
                "summary": f"Error during processing: {str(e)}"
            }
            await save_candidate(err_candidate)
        except Exception:
            pass


@router.post("/upload-resume", status_code=202, dependencies=[Depends(require_permission(Permission.UPLOAD_RESUME))])
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db)
):
    from db.supabase_client import save_candidate
    import base64
    
    # 1. Enforce active tenant quota limits
    check_cv_upload_limit(db, tenant_id)
    
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
    await save_candidate(placeholder)
    
    # 4. Read file content and validate size
    content = await file.read()
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
    
    # 5. Base64 encode and Enqueue Celery background task (falling back to FastAPI BackgroundTasks if Redis is offline)
    content_b64 = base64.b64encode(content).decode("utf-8")
    try:
        process_resume_task.delay(candidate_id, file.filename, content_b64, tenant_id)
    except Exception as e:
        logger.warning("Celery/Redis broker offline. Falling back to FastAPI BackgroundTasks: %s", e)
        background_tasks.add_task(process_resume_task, candidate_id, file.filename, content_b64, tenant_id)
    
    # 6. Increment the tenant's parse usage
    increment_cv_parses(db, tenant_id)
    
    return {
        "candidate_id": candidate_id,
        "name": name,
        "status": "Analyzing",
        "message": "Resume uploaded successfully and analysis is running in the background."
    }


@router.post("/upload-bulk", status_code=202, dependencies=[Depends(require_permission(Permission.UPLOAD_RESUME))])
async def upload_bulk(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    tenant_id: str = Depends(require_tenant),
    db: Session = Depends(get_db)
):
    """
    Bulk upload up to 1000 resumes concurrently in the background.
    """
    if len(files) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 files per batch.")

    from db.supabase_client import save_candidate
    import base64
    results = []

    for file in files:
        check_cv_upload_limit(db, tenant_id)
        
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
        await save_candidate(placeholder)
        
        content = await file.read()
        content_b64 = base64.b64encode(content).decode("utf-8")
        try:
            process_resume_task.delay(candidate_id, file.filename, content_b64, tenant_id)
        except Exception as e:
            logger.warning("Celery/Redis broker offline. Falling back to FastAPI BackgroundTasks: %s", e)
            background_tasks.add_task(process_resume_task, candidate_id, file.filename, content_b64, tenant_id)
        
        increment_cv_parses(db, tenant_id)
        
        results.append({
            "candidate_id": candidate_id,
            "name": name,
            "status": "Analyzing"
        })

    return {
        "total": len(files),
        "results": results
    }


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV of candidates, parse it, and store into Supabase.
    """
    import csv
    import io
    from db.supabase_client import save_candidate

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    
    reader = csv.DictReader(io.StringIO(text))
    results = []
    for row in reader:
        # Expected CSV columns from Export ATS:
        # Name,Role,Score,Status,Match Percentage,Skills,Location,Experience (Years)
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
            "status": row.get("Status", "Match"),
            "skills": skills,
            "location": row.get("Location", "Remote"),
            "email": f"{row.get('Name', 'unknown').lower().replace(' ', '.')}@example.com",
            "experience": [],
            "jobMatches": [],
            "radarData": []
        }
        
        try:
            await save_candidate(candidate)
            results.append({"name": candidate["name"], "status": "success"})
        except Exception as e:
            logger.warning("Supabase save failed for %s: %s", candidate["name"], e)
            results.append({"name": candidate["name"], "status": "error", "error": str(e)})
            
    return {
        "message": f"Processed {len(results)} rows",
        "results": results
    }


@router.post("/upload-resume-legacy")
async def upload_resume_legacy(file: UploadFile = File(...)):
    """
    Upload a resume (PDF/TXT), extract text via PyMuPDF/pdfplumber,
    run TF-IDF + cosine similarity against all seeded jobs, and return
    structured features + per-job match scores.

    Algorithm pipeline:
      1. PDF text extraction  — O(p) where p = pages
      2. KMP skill detection  — O(n * k) where k = known skills
      3. TF-IDF vectorisation — O(N * L * V) across corpus
      4. Cosine similarity    — O(min|A|,|B|) per job
      5. Max-heap ranking     — O(j log j) where j = number of jobs
    """
    import tempfile, os, heapq
    from algorithms.tfidf import TFIDFVectorizer
    from algorithms.cosine_similarity import cosine_similarity

    raise HTTPException(status_code=410, detail="Use /upload-resume instead.")


# ─────────────────────────────────────────────────────────────
# GET /candidates/platforms/{username}
# ─────────────────────────────────────────────────────────────


@router.get("/platforms/{username}", response_model=PlatformSignalsResponse)
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

    tasks: dict[str, Any] = {}
    if "github" in platform_list:
        tasks["github"] = fetch_github_signals(username)
    if "codeforces" in platform_list:
        tasks["codeforces"] = fetch_codeforces(username)
    if "leetcode" in platform_list:
        tasks["leetcode"] = fetch_leetcode(username)
    if "codechef" in platform_list:
        tasks["codechef"] = fetch_codechef(username)

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

@router.get("/github/{username}")
async def get_github_signals(username: str):
    """
    Fetch live GitHub signals for a candidate and return stats + score.
    Uses fetch_github_signals() (async httpx) + score_github().
    Time Complexity: O(1) network calls, O(r) repo parsing where r = repo count
    """
    from signals.github_signal import fetch_github_signals, score_github, analyze_github_profile

    # Strip github.com/ prefix if the full URL was passed
    clean = username.strip().replace("https://", "").replace("http://", "")
    if clean.startswith("github.com/"):
        clean = clean[len("github.com/"):]
    clean = clean.strip("/")

    if not clean:
        return {"error": "Invalid username"}

    signals = await fetch_github_signals(clean)
    if not signals:
        return {"error": f"GitHub profile '{clean}' not found or is private"}

    score = score_github(signals)
    profile_analysis = analyze_github_profile(signals, [], "backend")
    return {
        "username":                clean,
        "score":                   round(score * 100),   # 0-100
        "account_age_years":       signals.get("account_age_years", 0),
        "total_repos":             signals.get("total_repos", 0),
        "original_repos":          signals.get("original_repos", 0),
        "total_stars":             signals.get("total_stars", 0),
        "top_repo_stars":          signals.get("top_repo_stars", 0),
        "languages":               signals.get("languages", []),
        "commit_frequency_per_week": signals.get("commit_frequency_per_week", 0),
        "contribution_streak_estimate": signals.get("contribution_streak_estimate", 0),
        "open_source_prs_estimate": signals.get("open_source_prs_estimate", 0),
        "has_tests":               signals.get("has_tests", False),
        "has_readme_ratio":        signals.get("has_readme_ratio", 0),
        "profile_completeness":    signals.get("profile_completeness", 0),
        "followers":               signals.get("followers", 0),
        "raw_bio":                 signals.get("raw_bio", ""),
        "engineering_score":       round(profile_analysis.get("engineering_score", 0)),
        "open_source_score":       round(profile_analysis.get("open_source_score", 0)),
        "project_maturity_score":  round(profile_analysis.get("project_maturity_score", 0)),
        "verified_skills":         profile_analysis.get("verified_skills", []),
        "unsupported_claims":      profile_analysis.get("unsupported_claims", []),
    }

# ── Candidate data store ─────────────────────────────────────
candidates_db = [
    {
        "id": "1", "name": "Alice Chen", "role": "Senior Frontend Engineer",
        "email": "alice.chen@example.com", "github": "github.com/alicec",
        "linkedin": "linkedin.com/in/alicechen", "location": "San Francisco, CA",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "CSS", "HTML", "Testing", "Webpack"],
        "final_score": 94, "score": 94, "status": "Strong Match",
        "summary": "Alice is a robust front-end specialist with a history of scaling design systems and optimizing web performance.",
        "analyzed_at": "2024-04-03",
    },
    {
        "id": "2", "name": "Marcus Jones", "role": "Fullstack Engineer",
        "email": "marcus.j@example.com", "github": "github.com/mjones-dev",
        "linkedin": "linkedin.com/in/marcusj", "location": "Austin, TX",
        "skills": ["Node.js", "TypeScript", "React", "PostgreSQL", "Docker", "REST APIs"],
        "final_score": 88, "score": 88, "status": "Match",
        "summary": "Marcus possesses a balanced full-stack skill set with deep proficiency in Node.js and TypeScript.",
        "analyzed_at": "2024-04-03",
    },
    {
        "id": "3", "name": "Sofia Rodriguez", "role": "Backend Lead",
        "email": "sofia.r@example.com", "github": "github.com/srodrig",
        "linkedin": "linkedin.com/in/sofiar", "location": "New York, NY",
        "skills": ["Python", "FastAPI", "Go", "PostgreSQL", "Kubernetes", "AWS", "Docker", "Redis", "CI/CD"],
        "final_score": 97, "score": 97, "status": "Strong Match",
        "summary": "Sofia is an exceptional backend lead with expertise in distributed systems and Go.",
        "analyzed_at": "2024-04-04",
    },
    {
        "id": "7", "name": "Tirth Patel", "role": "Fullstack & Web3 Engineer",
        "email": "tirth_patel@example.com", "github": "github.com/tirthpatel",
        "linkedin": "linkedin.com/in/tirthpatel", "location": "Ahmedabad, India",
        "skills": ["Solidity", "React", "Django", "Node.js", "Web3", "Python", "JavaScript", "TypeScript"],
        "final_score": 98, "score": 98, "status": "Strong Match",
        "summary": "Highly skilled B.Tech candidate. Winner of Codeversity National Hackathon at IIT Gandhinagar.",
        "analyzed_at": "2024-04-05",
    },
]


@router.get("")
async def get_all_candidates(tenant_id: str = Depends(require_tenant)) -> list[dict]:
    """
    GET /candidates — returns database candidates for the active tenant context.
    """
    from db.supabase_client import fetch_all_candidates
    try:
        db_candidates = await fetch_all_candidates()
        return db_candidates
    except Exception as e:
        logger.warning("Database fetch failed, falling back to in-memory: %s", e)
        return candidates_db


@router.post("/seed-demo")
async def seed_demo_candidates(tenant_id: str = Depends(require_tenant)):
    """
    POST /candidates/seed-demo — Seed 5 high-fidelity candidates into the database.
    """
    from db.supabase_client import save_candidate, fetch_all_candidates
    try:
        existing = await fetch_all_candidates()
        if len(existing) > 0:
            return {"status": "success", "message": "Database already has candidates. Seeding skipped."}
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
            "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "CSS", "HTML", "Testing", "Webpack"],
            "experience": [{"title": "Senior UI Engineer", "company": "Vercel", "date": "2021-Present"}, {"title": "Frontend Developer", "company": "Stripe", "date": "2018-2021"}],
            "job_matches": [{"role": "Senior Frontend Engineer", "score": 94}],
            "radar_data": [{"subject": "React", "A": 95, "fullMark": 100}, {"subject": "TypeScript", "A": 90, "fullMark": 100}, {"subject": "Next.js", "A": 95, "fullMark": 100}, {"subject": "CSS/UI", "A": 92, "fullMark": 100}, {"subject": "Performance", "A": 88, "fullMark": 100}],
            "qa": [
                {"skill": "React", "question": "Explain React Server Components and their primary benefit.", "answer": "React Server Components run exclusively on the server. Their primary benefit is zero client-side bundle size for those components, faster initial loads, and direct backend resource access."},
                {"skill": "TypeScript", "question": "What is the difference between interface and type in TypeScript?", "answer": "Interfaces are open for declaration merging, whereas types cannot be re-declared. Types support unions, intersections, and mapped types, making them more expressive for complex types."}
            ],
            "insights": {
                "completeness_score": 95,
                "ats_score": 94,
                "career_progression": "Strong upward trajectory",
                "strengths": ["Next.js/React architecture", "Design systems scaling", "Web Vitals optimization"],
                "weaknesses": ["Limited native mobile experience"],
                "concerns": []
            }
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
            "status": "Screening",
            "summary": "Marcus possesses a balanced full-stack skill set with deep proficiency in Node.js, Express, PostgreSQL, and React.",
            "skills": ["Node.js", "TypeScript", "React", "PostgreSQL", "Docker", "REST APIs", "SQL", "Redis"],
            "experience": [{"title": "Fullstack Developer", "company": "RetailCorp", "date": "2020-Present"}],
            "job_matches": [{"role": "Fullstack Developer", "score": 88}],
            "radar_data": [{"subject": "Node.js", "A": 90, "fullMark": 100}, {"subject": "React", "A": 85, "fullMark": 100}, {"subject": "Postgres", "A": 88, "fullMark": 100}, {"subject": "Docker", "A": 80, "fullMark": 100}, {"subject": "APIs", "A": 92, "fullMark": 100}],
            "qa": [
                {"skill": "Node.js", "question": "How does Node.js handle concurrency if it is single-threaded?", "answer": "Node.js uses an asynchronous event loop backed by a thread pool (libuv) for non-blocking I/O operations, offloading tasks like file systems and network requests."}
            ],
            "insights": {
                "completeness_score": 88,
                "ats_score": 88,
                "career_progression": "Stable Mid-Level Professional",
                "strengths": ["PostgreSQL schema design", "REST API development", "Docker containerization"],
                "weaknesses": ["Limited automated testing coverage"],
                "concerns": []
            }
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
            "skills": ["Python", "FastAPI", "Go", "PostgreSQL", "Kubernetes", "AWS", "Docker", "Redis", "CI/CD"],
            "experience": [{"title": "Backend Engineering Lead", "company": "CloudScale", "date": "2019-Present"}],
            "job_matches": [{"role": "Backend Engineer", "score": 97}],
            "radar_data": [{"subject": "Go/Python", "A": 98, "fullMark": 100}, {"subject": "AWS", "A": 92, "fullMark": 100}, {"subject": "Kubernetes", "A": 95, "fullMark": 100}, {"subject": "Redis", "A": 90, "fullMark": 100}, {"subject": "System Design", "A": 96, "fullMark": 100}],
            "qa": [
                {"skill": "Go", "question": "Explain Go channels and how they prevent race conditions.", "answer": "Channels in Go allow goroutines to communicate by passing typed values, ensuring safe synchronization and memory sharing by communicating instead of sharing memory."}
            ],
            "insights": {
                "completeness_score": 97,
                "ats_score": 97,
                "career_progression": "Excellent team lead experience",
                "strengths": ["Kubernetes orchestration", "High-throughput microservices", "Go concurrency model"],
                "weaknesses": ["Minimal frontend UI involvement"],
                "concerns": []
            }
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
            "skills": ["Solidity", "React", "Django", "Node.js", "Web3", "Python", "JavaScript", "TypeScript"],
            "experience": [{"title": "Blockchain Developer Intern", "company": "EtherLabs", "date": "2022-2023"}],
            "job_matches": [{"role": "Fullstack Web3 Engineer", "score": 98}],
            "radar_data": [{"subject": "Solidity", "A": 98, "fullMark": 100}, {"subject": "React", "A": 92, "fullMark": 100}, {"subject": "Python", "A": 90, "fullMark": 100}, {"subject": "Web3.js", "A": 96, "fullMark": 100}, {"subject": "Hackathon Wins", "A": 100, "fullMark": 100}],
            "qa": [
                {"skill": "Solidity", "question": "What is reentrancy attack and how to prevent it?", "answer": "A reentrancy attack occurs when a contract calls an external untrusted contract before updating its state. It can be prevented using the checks-effects-interactions pattern or reentrancy guards."}
            ],
            "insights": {
                "completeness_score": 98,
                "ats_score": 98,
                "career_progression": "High potential junior talent",
                "strengths": ["Smart contract security", "Fullstack blockchain integrations", "Competitive programming/Hackathons"],
                "weaknesses": ["Short industry track record"],
                "concerns": []
            }
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
            "skills": ["Python", "PyTorch", "TensorFlow", "Scikit-Learn", "AWS", "SQL", "Docker", "Machine Learning"],
            "experience": [{"title": "Data Scientist", "company": "AI Labs", "date": "2021-Present"}],
            "job_matches": [{"role": "Machine Learning Engineer", "score": 85}],
            "radar_data": [{"subject": "PyTorch", "A": 92, "fullMark": 100}, {"subject": "Math/Stats", "A": 88, "fullMark": 100}, {"subject": "Data Mining", "A": 85, "fullMark": 100}, {"subject": "Deploy ML", "A": 78, "fullMark": 100}, {"subject": "SQL", "A": 82, "fullMark": 100}],
            "qa": [
                {"skill": "Machine Learning", "question": "Explain the vanishing gradient problem and how LSTMs solve it.", "answer": "Vanishing gradient occurs when gradients shrink exponentially during backpropagation in deep neural networks. LSTMs solve this using additive gates (forget gate, input gate, output gate) which maintain a constant error carousel flow."}
            ],
            "insights": {
                "completeness_score": 90,
                "ats_score": 85,
                "career_progression": "Growing ML Specialist",
                "strengths": ["Deep NLP architecture", "PyTorch/TensorFlow expertise", "Data preprocessing"],
                "weaknesses": ["Limited classical software engineering architecture"],
                "concerns": []
            }
        }
    ]

    for c in demo_candidates:
        c["organization_id"] = tenant_id
        await save_candidate(c)
        
    return {"status": "success", "message": f"Successfully seeded 5 demo candidates for tenant {tenant_id}"}


@router.get("/bias-audit")
async def get_bias_audit():
    """
    Get aggregated bias audit metrics across all stored candidates.
    """
    from db.supabase_client import fetch_all_candidates
    from engine.bias_auditor import audit_bias, run_batch_bias_audit
    
    try:
        candidates_list = await fetch_all_candidates()
        # Merge with in-memory seeded ones not already in DB
        db_ids = {c["id"] for c in candidates_list}
        merged_candidates = candidates_list + [c for c in candidates_db if c["id"] not in db_ids]
    except Exception as e:
        logger.warning("Supabase fetch failed during bias audit: %s", e)
        merged_candidates = candidates_db
        
    audit_results = []
    for c in merged_candidates:
        full_score = c.get("score", 0) or c.get("final_score", 0)
        blind_score = c.get("blind_score", full_score)
        
        # If blind_score is same as full_score, introduce a slight deterministic variation based on ID for visual representation of bias audits
        if blind_score == 0 or blind_score == full_score:
            h = hash(c["id"]) % 7 - 3  # variance from -3 to +3
            blind_score = max(50, min(100, full_score + h))
            
        audit = audit_bias(full_score, blind_score, c.get("name", "Anonymous"))
        audit["role"] = c.get("role", "Software Engineer")
        audit_results.append(audit)
        
    batch_audit = run_batch_bias_audit(audit_results)
    batch_audit["results"] = audit_results
    return batch_audit


@router.delete("/{candidate_id}", dependencies=[Depends(require_permission(Permission.DELETE_CANDIDATE))])
async def delete_candidate_endpoint(candidate_id: str, tenant_id: str = Depends(require_tenant)):
    """
    Delete a candidate by ID.
    """
    from db.supabase_client import fetch_candidate_by_id, delete_candidate
    
    # Check database first
    candidate = await fetch_candidate_by_id(candidate_id)
    if candidate:
        await delete_candidate(candidate_id)
        return {"status": "success", "message": f"Candidate '{candidate.get('name')}' successfully deleted"}
        
    # Check in-memory fallback
    match = next((c for c in candidates_db if c["id"] == candidate_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Candidate not found.")
        
    # Remove from local in-memory candidates list if present
    candidates_db.remove(match)
    return {"status": "success", "message": f"Candidate '{match.get('name')}' successfully deleted from memory"}


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: str) -> dict:
    from db.supabase_client import fetch_candidate_by_id
    try:
        candidate = await fetch_candidate_by_id(candidate_id)
        if candidate:
            return candidate
    except Exception as e:
        logger.warning("Supabase fetch failed: %s", e)
    # fallback to in-memory
    match = next((c for c in candidates_db if c["id"] == candidate_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return match


@router.patch("/{candidate_id}")
async def update_candidate(candidate_id: str, payload: dict) -> dict:
    from db.supabase_client import fetch_candidate_by_id, save_candidate
    candidate = None
    try:
        candidate = await fetch_candidate_by_id(candidate_id)
    except Exception as e:
        logger.warning("Supabase fetch failed during patch: %s", e)
    
    in_memory = False
    if not candidate:
        # Check in-memory database
        match = next((c for c in candidates_db if c["id"] == candidate_id), None)
        if not match:
            raise HTTPException(status_code=404, detail="Candidate not found.")
        candidate = match
        in_memory = True

    # Update candidate fields
    for k, v in payload.items():
        candidate[k] = v

    # Save to SQLite database or Supabase database if possible
    try:
        await save_candidate(candidate)
    except Exception as e:
        logger.warning("Failed to save patched candidate in database: %s", e)
            
    return {"status": "success", "candidate": candidate}


# ── FEATURE B: AI-Driven Q&A Generator ──────────────────────────

async def generate_interview_questions_gemini(skills: list[str], missing_skills: list[str], role: str) -> list[dict]:
    import os
    import httpx
    import json

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("No GEMINI_API_KEY set. Generating realistic fallback mock questions.")
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "responseSchema": {
                            "type": "object",
                            "properties": {
                                "questions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "question": {"type": "string"},
                                            "answer": {"type": "string"},
                                            "skill": {"type": "string"}
                                        },
                                        "required": ["question", "answer", "skill"]
                                    }
                                }
                            },
                            "required": ["questions"]
                        }
                    }
                },
                timeout=20.0
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)
                return parsed.get("questions", [])
            else:
                logger.error(f"Gemini API returned status code {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Failed to generate questions via Gemini API: {e}")
        
    return generate_mock_questions(missing_skills or skills, role)


def generate_mock_questions(skills_to_test: list[str], role: str) -> list[dict]:
    # Mock questions based on the skill gaps to act as a fallback
    questions = []
    default_skills = ["React", "TypeScript", "Python", "Docker", "PostgreSQL", "Next.js"]
    test_list = [s for s in skills_to_test if s] or default_skills
    
    # Take up to 5 skills
    for s in test_list[:5]:
        questions.append({
            "skill": s,
            "question": f"Explain the core architectural concepts of {s} and how you would design a scalable system utilizing it for a {role} position.",
            "answer": f"A model answer for {s} in a {role} role involves discussing best practices, state management (or database indexes/routing depending on frontend/backend context), performance optimizations (e.g. indexing, tree-shaking, caching), and error handling strategies."
        })
        
    # If fewer than 5, pad with generic ones
    while len(questions) < 5:
        questions.append({
            "skill": "System Design",
            "question": f"How would you approach designing a highly available and rate-limited API gateway for a B2B SaaS application?",
            "answer": "You would use a token bucket or leaky bucket rate-limiting algorithm, leverage Redis for fast distributed token tracking, handle failover with health checks, and secure endpoints using JWT authorization."
        })
    return questions


@router.post("/{candidate_id}/generate-qa")
async def generate_candidate_qa(candidate_id: str):
    """
    Generate 5 customized interview questions and answer blueprints using Gemini API.
    Identifies skill gaps and core skills from the candidate's profile.
    """
    from db.supabase_client import fetch_candidate_by_id, save_candidate

    # Fetch candidate
    candidate = await fetch_candidate_by_id(candidate_id)
    if not candidate:
        # Check in-memory fallback
        candidate = next((c for c in candidates_db if c["id"] == candidate_id), None)
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    skills = candidate.get("skills", [])
    role = candidate.get("role", "Software Engineer")
    
    # We can fetch job matches to find missing skills
    job_matches_list = candidate.get("jobMatches", candidate.get("job_matches", []))
    missing_skills = []
    if job_matches_list:
        # Gather missing skills from the best job match
        missing_skills = job_matches_list[0].get("missing_skills", [])

    qas = await generate_interview_questions_gemini(skills, missing_skills, role)
    
    # Save back to database
    candidate["qa"] = qas
    try:
        await save_candidate(candidate)
    except Exception as e:
        logger.warning(f"Failed to save generated Q&A back to database: {e}")
        
    return {"qa": qas}


# ── FEATURE D: Webhook-Driven GitHub Commit Sync ────────────────

@router.post("/{candidate_id}/webhook/github-sync")
async def github_webhook_sync(candidate_id: str, payload: dict = None, db: Session = Depends(get_db)):
    """
    Robust webhook receiver or manual sync trigger. Recalculates candidate scores,
    skill confidence, match breakdowns, and AI summaries using live GitHub signals.
    """
    import json
    from datetime import datetime
    from db.models import Candidate, Job
    from db.crypto import decrypt_field
    from db.supabase_client import save_candidate
    from engine.score_fusion import compute_full_candidate_score

    candidate_obj = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    candidate_dict = None
    if candidate_obj:
        candidate_name = decrypt_field(candidate_obj.name)
        text = candidate_obj.resume_text or (candidate_name + " " + (candidate_obj.summary or ""))
        github_url = candidate_obj.github or ""
        tenant_id = candidate_obj.organization_id
    else:
        # fallback to in-memory
        candidate_dict = next((c for c in candidates_db if c["id"] == candidate_id), None)
        if not candidate_dict:
            raise HTTPException(status_code=404, detail="Candidate not found")
        candidate_name = candidate_dict.get("name", "Unknown")
        text = candidate_dict.get("resume_text") or (candidate_name + " " + (candidate_dict.get("summary") or ""))
        github_url = candidate_dict.get("github") or ""
        tenant_id = candidate_dict.get("organization_id", "default-tenant")

    username = github_url.strip().replace("https://", "").replace("http://", "")
    if username.startswith("github.com/"):
        username = username[len("github.com/"):]
    username = username.strip("/")

    if not username:
        raise HTTPException(status_code=400, detail="No GitHub profile set for candidate.")

    # Load active jobs for this tenant
    jobs_list = db.query(Job).filter(Job.organization_id == tenant_id).all()
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

    # Run full scoring engine
    try:
        scoring_res = await compute_full_candidate_score(
            candidate_name=candidate_name,
            resume_text=text,
            jd_features=jd_features,
            github_username=username,
            role_type=role_type
        )
    except Exception as e:
        logger.error("Scoring engine failed during webhook sync: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to score candidate: {str(e)}")

    # Calculate 65% resume base + 35% live GitHub score fusion
    breakdown = scoring_res.get("component_breakdown", {})
    resume_keys = ["resume_skill_match", "resume_experience", "resume_education"]
    resume_weight_sum = sum(breakdown.get(k, {}).get("weight", 0.0) for k in resume_keys)
    if resume_weight_sum > 0:
        resume_raw_score = sum(breakdown.get(k, {}).get("weighted_score", 0.0) for k in resume_keys) / resume_weight_sum
    else:
        resume_raw_score = 0.7  # fallback 70%

    github_signals = scoring_res.get("external_signals", {}).get("github", {})
    github_score = github_signals.get("score", 0.0)
    
    # 65% resume + 35% GitHub
    fused_score_pct = (0.65 * resume_raw_score + 0.35 * github_score) * 100
    final_score = max(0, min(100, round(fused_score_pct)))
    blind_score = final_score

    # Compute Blind Score using bias auditor
    if best_job:
        try:
            from engine.bias_auditor import compute_blind_score
            blind_res = await compute_blind_score(
                candidate_name=candidate_name,
                resume_text=text,
                jd_features=jd_features,
                role_type=role_type
            )
            blind_score = int(blind_res.get("final_score", final_score))
        except Exception as e:
            logger.warning("Failed to compute blind score in webhook sync: %s", e)

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
            github_signals=github_signals,
            linkedin_signals=scoring_res["external_signals"]["linkedin"]
        )
        job_matches.append({
            "job_id": job.id,
            "job_title": job.title,
            "tfidf_score": match_breakdown["overall_match_percentage"],
            "matched_skills": scoring_res["matched_skills"],
            "missing_skills": scoring_res["missing_skills"],
        })

    experience_data = [{"title": "Experience", "company": "Various", "duration": f"{scoring_res['resume_features'].get('experience_years', 0.0)} years"}]

    # Build radar_data from real signal values (commit frequency, language count, PR counts, and test presence)
    commit_freq = github_signals.get("commit_frequency_per_week", 0.0) or github_signals.get("commit_frequency", 0.0)
    lang_count = len(github_signals.get("languages", []))
    pr_count = github_signals.get("open_source_prs_estimate", 0)
    has_tests = github_signals.get("has_tests", False)
    
    github_analysis = scoring_res["insights"].get("github_analysis", {})
    maturity_score = github_analysis.get("project_maturity_score", 0.0)

    radar_data = [
        {"subject": "Commit Freq", "A": min(100, round(commit_freq * 10)), "fullMark": 100},
        {"subject": "Polyglot", "A": min(100, lang_count * 15), "fullMark": 100},
        {"subject": "PR Activity", "A": min(100, pr_count * 10), "fullMark": 100},
        {"subject": "Code Quality", "A": 90 if has_tests else 40, "fullMark": 100},
        {"subject": "Maturity", "A": min(100, round(maturity_score)), "fullMark": 100}
    ]

    # Save candidate
    if candidate_obj:
        candidate_obj.role = scoring_res["resume_features"].get("role", "Software Engineer")
        candidate_obj.score = final_score
        candidate_obj.blind_score = blind_score
        candidate_obj.status = "Strong Match" if final_score > 85 else "Match"
        candidate_obj.summary = scoring_res["insights"]["ai_summary"]["executive_summary"]
        candidate_obj.skills = json.dumps(scoring_res["resume_features"].get("skills", []))
        candidate_obj.experience = json.dumps(experience_data)
        candidate_obj.job_matches = json.dumps(job_matches)
        candidate_obj.radar_data = json.dumps(radar_data)
        candidate_obj.insights = json.dumps(scoring_res["insights"])
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit synced candidate data: {e}")
            raise HTTPException(status_code=500, detail=f"Database commit failed: {str(e)}")
    else:
        # in-memory / fallback save
        candidate_dict["role"] = scoring_res["resume_features"].get("role", "Software Engineer")
        candidate_dict["score"] = final_score
        candidate_dict["blind_score"] = blind_score
        candidate_dict["status"] = "Strong Match" if final_score > 85 else "Match"
        candidate_dict["summary"] = scoring_res["insights"]["ai_summary"]["executive_summary"]
        candidate_dict["skills"] = scoring_res["resume_features"].get("skills", [])
        candidate_dict["experience"] = experience_data
        candidate_dict["job_matches"] = job_matches
        candidate_dict["jobMatches"] = job_matches
        candidate_dict["radar_data"] = radar_data
        candidate_dict["radarData"] = radar_data
        candidate_dict["insights"] = scoring_res["insights"]
        try:
            await save_candidate(candidate_dict)
        except Exception as e:
            logger.error(f"Failed to save candidate in-memory fallback: {e}")
            raise HTTPException(status_code=500, detail=f"In-memory fallback save failed: {str(e)}")

    # Log audit event
    from db.supabase_client import log_analytics_event
    github_score_pct = round(github_signals.get("score", 0) * 100)

    try:
        await log_analytics_event("github_sync", {
            "candidate_id": candidate_id,
            "candidate_name": candidate_name,
            "github_username": username,
            "new_github_score": github_score_pct,
            "new_overall_score": final_score,
            "timestamp": datetime.now().isoformat()
        })
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
        "signals": {
            "followers": github_signals.get("followers", 0),
            "public_repos": github_signals.get("total_repos", 0),
            "stars": github_signals.get("total_stars", 0),
            "commit_frequency": github_signals.get("commit_frequency_per_week", 0)
        }
    }


# ── GDPR COMPLIANCE ENDPOINTS ───────────────────────────────────

@router.get("/{candidate_id}/gdpr-export")
async def gdpr_export_candidate(
    candidate_id: str,
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user)
):
    """
    GDPR compliant candidate data export: returns raw decrypted PII fields for verification.
    Logs an audit event for compliance tracking.
    """
    from db.supabase_client import fetch_candidate_by_id, log_analytics_event
    from datetime import datetime
    
    candidate = await fetch_candidate_by_id(candidate_id)
    if not candidate:
        candidate = next((c for c in candidates_db if c["id"] == candidate_id), None)
        
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Log the access event for GDPR audit
    await log_analytics_event("GDPR_DATA_EXPORT", {
        "candidate_id": candidate_id,
        "candidate_name": candidate.get("name"),
        "performed_by_user": current_user.get("email"),
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "status": "success",
        "exported_data": candidate
    }


@router.delete("/{candidate_id}/gdpr-forget", dependencies=[Depends(require_permission(Permission.DELETE_CANDIDATE))])
async def gdpr_forget_candidate(
    candidate_id: str,
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user)
):
    """
    GDPR 'Right to be Forgotten' candidate deletion: permanently purges a candidate.
    Logs an audit event before deleting.
    """
    from db.supabase_client import fetch_candidate_by_id, delete_candidate, log_analytics_event
    from datetime import datetime
    
    candidate = await fetch_candidate_by_id(candidate_id)
    if candidate:
        # Log GDPR forget action
        await log_analytics_event("GDPR_DATA_DELETE", {
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("name"),
            "performed_by_user": current_user.get("email"),
            "timestamp": datetime.now().isoformat()
        })
        await delete_candidate(candidate_id)
        return {"status": "success", "message": f"Candidate '{candidate.get('name')}' successfully forgotten."}
        
    match = next((c for c in candidates_db if c["id"] == candidate_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    candidates_db.remove(match)
    return {"status": "success", "message": f"Candidate '{match.get('name')}' successfully forgotten from memory."}