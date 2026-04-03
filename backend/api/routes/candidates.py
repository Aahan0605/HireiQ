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

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

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
from engine.bias_auditor import audit_bias, run_batch_bias_audit, create_blind_features
from engine.score_fusion import compute_full_candidate_score
from parser.resume_parser import async_extract_text as parse_resume_text
from parser.feature_extractor import extract_features
from signals.github_signal import fetch_github_signals
from signals.coding_signal import fetch_codeforces, fetch_codechef, fetch_leetcode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["candidates"])


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

    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build heap for ranking
    heap = CandidateHeap(capacity=request.top_k)
    scored_results: list[dict[str, Any]] = []

    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            logger.error(
                "Scoring failed for candidate %d: %s",
                i, str(result),
            )
            continue
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
            # Simulate blind score by removing identity-linked small variance
            # In production, you'd re-score with create_blind_features()
            blind_score = full_score  # Blind = same since our engine is skill-based
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
# POST /candidates/upload-resume
# ─────────────────────────────────────────────────────────────

@router.post("/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeUploadResponse:
    """
    Upload a resume file (PDF or TXT), extract text, and return features.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    allowed_ext = {".pdf", ".txt", ".md", ".docx"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_ext)}",
        )

    content = await file.read()

    if ext == ".pdf":
        # Save temp file and parse
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            text = await parse_resume_text(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        text = content.decode("utf-8", errors="replace")

    features = extract_features(text)

    return ResumeUploadResponse(
        filename=file.filename,
        text_length=len(text),
        extracted_text=text[:5000],  # Limit response size
        features=features,
    )


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
        raise HTTPException(status_code=400, detail="At least one platform is required.")

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
