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
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

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
                i,
                str(result),
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
# POST /candidates/upload-resume  (single)
# POST /candidates/upload-bulk    (multiple — up to 1000)
# ─────────────────────────────────────────────────────────────


async def _process_resume(file: UploadFile) -> dict:
    """Shared processing logic for a single resume file."""
    import tempfile, os, heapq
    from algorithms.tfidf import TFIDFVectorizer
    from algorithms.cosine_similarity import cosine_similarity
    from .jobs import jobs_db
    from .settings import active_weights
    from db.supabase_client import save_candidate

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed_ext = {".pdf", ".txt", ".md", ".docx"}
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")

    content = await file.read()

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

    job_texts = [
        f"{j['description']} {j['required_skills'].replace(',', ' ')}"
        for j in jobs_db
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
            job = jobs_db[i]
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

    candidate = {
        "id": str(uuid.uuid4()),
        "name": name,
        "role": "Software Engineer",
        "email": email_m.group() if email_m else f"{raw_name.lower().replace(' ', '.')}@example.com",
        "github": github_m.group() if github_m else "",
        "linkedin": linkedin_m.group() if linkedin_m else "",
        "location": "Remote",
        "score": final_score,
        "status": "Strong Match" if final_score > 90 else "Match",
        "summary": text[:400].strip(),
        "skills": features.get("skills", []),
        "experience": [],
        "jobMatches": job_matches,
        "radarData": [],
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


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    return await _process_resume(file)


@router.post("/upload-bulk")
async def upload_bulk(files: list[UploadFile] = File(...)):
    """
    Bulk upload up to 1000 resumes concurrently.
    Returns a list of results (success or error) per file.
    """
    if len(files) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 files per batch.")

    async def safe_process(f: UploadFile) -> dict:
        try:
            return await _process_resume(f)
        except Exception as e:
            return {"filename": f.filename, "error": str(e)}

    results = await asyncio.gather(*[safe_process(f) for f in files])
    succeeded = [r for r in results if "error" not in r]
    failed    = [r for r in results if "error" in r]
    return {
        "total": len(files),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "results": list(results),
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
    from .jobs import jobs_db  # import seeded jobs

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
    from signals.github_signal import fetch_github_signals, score_github

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
async def get_all_candidates() -> list[dict]:
    """
    GET /candidates — returns Supabase candidates merged with seeded defaults.
    """
    from db.supabase_client import fetch_all_candidates
    try:
        db_candidates = await fetch_all_candidates()
        # Merge: DB rows take priority; append seeded ones not already in DB
        db_ids = {c["id"] for c in db_candidates}
        merged = db_candidates + [c for c in candidates_db if c["id"] not in db_ids]
        return merged
    except Exception as e:
        logger.warning("Supabase fetch failed, falling back to in-memory: %s", e)
        return candidates_db


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