"""
Score Fusion Engine — Combine all signals into a single candidate score.

Orchestrates:
    1. Resume parsing & feature extraction
    2. Concurrent external signal fetching (GitHub, competitive, portfolio)
    3. Claim verification
    4. Role-weighted score fusion
    5. Trust-adjusted final scoring
    6. Actionable recommendation generation
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from config import (
    SCORING_WEIGHTS,
    ROLE_WEIGHT_PROFILES,
)
from parser.feature_extractor import extract_features
from algorithms.tfidf import TFIDFVectorizer
from algorithms.cosine_similarity import (
    cosine_similarity as cosine_similarity_sparse,
)
from signals.github_signal import fetch_github_signals, score_github
from signals.coding_signal import (
    fetch_codeforces,
    fetch_codechef,
    fetch_leetcode,
    score_competitive_coding,
)
from signals.portfolio_crawler import crawl_portfolio, score_portfolio
from signals.linkedin_signal import (
    extract_linkedin_signals_from_resume,
    score_linkedin,
)
from signals.cert_verifier import (
    detect_certifications,
    score_certifications,
)
from engine.claim_verifier import verify_claims

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Main orchestrator
# ─────────────────────────────────────────────────────────────


async def compute_full_candidate_score(
    candidate_name: str,
    resume_text: str,
    jd_features: dict[str, Any],
    github_username: str | None = None,
    cf_handle: str | None = None,
    cc_username: str | None = None,
    lc_username: str | None = None,
    portfolio_url: str | None = None,
    role_type: str = "backend_engineer",
) -> dict[str, Any]:
    """
    Compute the complete 360° candidate intelligence score.

    Args:
        candidate_name:  Candidate's full name.
        resume_text:     Raw resume text (already extracted from PDF/TXT).
        jd_features:     Job description features dict with keys:
                         required_skills, preferred_skills, min_experience, etc.
        github_username: Optional GitHub username.
        cf_handle:       Optional Codeforces handle.
        cc_username:     Optional CodeChef username.
        lc_username:     Optional LeetCode username.
        portfolio_url:   Optional portfolio website URL.
        role_type:       Role type key from ROLE_WEIGHT_PROFILES.

    Returns:
        Comprehensive result dict with final_score, breakdowns,
        trust analysis, recommendations, and all raw signals.
    """

    # ── Step 1: Extract resume features ──
    resume_features = extract_features(resume_text)
    claimed_skills = resume_features.get("skills", [])
    claimed_experience = resume_features.get("experience", 0.0)
    claimed_education = resume_features.get("education", [])
    claimed_certs = resume_features.get("certifications", [])

    # ── Step 2: Compute resume-based scores ──
    base_scores = _compute_resume_scores(
        resume_features,
        jd_features,
        resume_text,
    )

    # ── Step 3: Fetch external signals concurrently ──
    external_signals = await _fetch_all_external_signals(
        resume_text=resume_text,
        github_username=github_username,
        cf_handle=cf_handle,
        cc_username=cc_username,
        lc_username=lc_username,
        portfolio_url=portfolio_url,
        claimed_skills=claimed_skills,
    )

    # ── Step 4: Score external signals ──
    signal_scores = _score_external_signals(
        external_signals,
        claimed_skills,
        role_type,
    )

    # ── Step 5: Verify claims ──
    trust_result = verify_claims(resume_features, external_signals)

    # ── Step 6: Compute weighted final score ──
    role_weights = ROLE_WEIGHT_PROFILES.get(
        role_type, ROLE_WEIGHT_PROFILES.get("backend_engineer", SCORING_WEIGHTS)
    )

    all_scores = {**base_scores, **signal_scores}
    component_breakdown = _build_component_breakdown(all_scores, role_weights)
    weighted_raw = sum(
        entry["weighted_score"] for entry in component_breakdown.values()
    )

    # ── Step 7: Apply trust multiplier ──
    # Trust can reduce score by max 30%
    trust_score = trust_result.get("trust_score", 1.0)
    trust_multiplier = 0.7 + 0.3 * trust_score
    final_score = round(weighted_raw * trust_multiplier * 100, 2)
    final_score = max(0.0, min(100.0, final_score))

    # ── Step 8: Compute skill matching ──
    jd_required = {s.lower() for s in jd_features.get("required_skills", [])}
    jd_preferred = {s.lower() for s in jd_features.get("preferred_skills", [])}
    all_jd_skills = jd_required | jd_preferred
    claimed_lower = {s.lower() for s in claimed_skills}
    matched_skills = sorted(all_jd_skills & claimed_lower)
    missing_skills = sorted(all_jd_skills - claimed_lower)

    # ── Step 9: Generate recommendations ──
    low_scores = {
        k: v for k, v in all_scores.items() if v < 0.4 and role_weights.get(k, 0) > 0.05
    }
    recommendations = generate_recommendations(
        missing_skills=missing_skills,
        low_scores=low_scores,
        trust_result=trust_result,
        external_signals=external_signals,
    )

    return {
        "candidate_name": candidate_name,
        "role_type": role_type,
        "final_score": final_score,
        "trust_multiplier": round(trust_multiplier, 4),
        "component_breakdown": component_breakdown,
        "trust_result": {
            "trust_score": trust_result["trust_score"],
            "flags": trust_result["flags"],
            "verdict": trust_result["verdict"],
            "verified_skills": trust_result["verified_skills"],
            "flagged_skills": trust_result["flagged_skills"],
        },
        "resume_features": {
            "skills": claimed_skills,
            "experience_years": claimed_experience,
            "education": claimed_education,
            "certifications": claimed_certs,
        },
        "external_signals": {
            "github": external_signals.get("github", {}),
            "competitive": {
                "codeforces": external_signals.get("codeforces", {}),
                "codechef": external_signals.get("codechef", {}),
                "leetcode": external_signals.get("leetcode", {}),
            },
            "portfolio": external_signals.get("portfolio", {}),
            "linkedin": external_signals.get("linkedin", {}),
        },
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendations,
    }


# ─────────────────────────────────────────────────────────────
# Resume-based scoring
# ─────────────────────────────────────────────────────────────


def _compute_resume_scores(
    resume_features: dict,
    jd_features: dict,
    resume_text: str,
) -> dict[str, float]:
    """Compute all resume-derived scores."""
    scores: dict[str, float] = {}

    # Skill match score via TF-IDF + cosine similarity
    # ONLY compute if job description is provided with skills
    jd_skills = jd_features.get("required_skills", []) + jd_features.get(
        "preferred_skills", []
    )
    resume_skills = resume_features.get("skills", [])

    if jd_skills and resume_skills:
        jd_text = " ".join(jd_skills)
        resume_skill_text = " ".join(resume_skills)
        vectorizer = TFIDFVectorizer()
        vectorizer.fit([jd_text, resume_skill_text])
        vecs = vectorizer.transform([jd_text, resume_skill_text])
        if len(vecs) >= 2:
            sim = cosine_similarity_sparse(vecs[0], vecs[1])
        else:
            sim = 0.0

        # Also compute direct overlap ratio
        required_set = {s.lower() for s in jd_features.get("required_skills", [])}
        candidate_set = {s.lower() for s in resume_skills}
        if required_set:
            overlap = len(required_set & candidate_set) / len(required_set)
        else:
            overlap = 0.0

        scores["resume_skill_match"] = round(0.6 * sim + 0.4 * overlap, 4)
    elif not jd_skills:
        # No job description provided — score is N/A, not a default 0.5
        scores["resume_skill_match"] = None
    else:
        scores["resume_skill_match"] = 0.0

    # Experience score
    claimed_exp = resume_features.get("experience", 0.0)
    min_exp = jd_features.get("min_experience", 0)
    max_exp = jd_features.get("max_experience", 15)

    if max_exp > 0:
        if claimed_exp >= min_exp:
            exp_ratio = min(claimed_exp / max(max_exp, 1), 1.0)
            scores["resume_experience"] = round(0.5 + 0.5 * exp_ratio, 4)
        else:
            scores["resume_experience"] = round(
                max(0.0, claimed_exp / max(min_exp, 1) * 0.5), 4
            )
    else:
        scores["resume_experience"] = 0.5

    # Education score
    education = resume_features.get("education", [])
    edu_score = 0.0
    degree_weights = {
        "phd": 1.0,
        "doctorate": 1.0,
        "master": 0.85,
        "ms": 0.85,
        "mtech": 0.85,
        "mca": 0.80,
        "bachelor": 0.65,
        "bs": 0.65,
        "btech": 0.65,
        "bca": 0.60,
        "be": 0.65,
        "associate": 0.40,
        "diploma": 0.35,
    }
    for edu in education:
        edu_lower = edu.lower() if isinstance(edu, str) else ""
        for degree, weight in degree_weights.items():
            if degree in edu_lower:
                edu_score = max(edu_score, weight)
                break
    scores["resume_education"] = round(edu_score, 4)

    return scores


# ─────────────────────────────────────────────────────────────
# External signal fetching
# ─────────────────────────────────────────────────────────────


async def _fetch_all_external_signals(
    resume_text: str,
    github_username: str | None,
    cf_handle: str | None,
    cc_username: str | None,
    lc_username: str | None,
    portfolio_url: str | None,
    claimed_skills: list[str],
) -> dict[str, Any]:
    """Fetch all external signals concurrently."""
    signals: dict[str, Any] = {}
    tasks: dict[str, Any] = {}

    # GitHub
    if github_username:
        tasks["github"] = fetch_github_signals(github_username)

    # Competitive coding — launch all concurrently
    if cf_handle:
        tasks["codeforces"] = fetch_codeforces(cf_handle)
    if cc_username:
        tasks["codechef"] = fetch_codechef(cc_username)
    if lc_username:
        tasks["leetcode"] = fetch_leetcode(lc_username)

    # Portfolio
    if portfolio_url:
        tasks["portfolio"] = crawl_portfolio(portfolio_url)

    # Execute all async tasks concurrently
    if tasks:
        keys = list(tasks.keys())
        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )
        for key, result in zip(keys, results):
            if isinstance(result, Exception):
                logger.warning("Signal fetch failed for %s: %s", key, str(result))
                signals[key] = {}
            else:
                signals[key] = result if result else {}

    # LinkedIn (synchronous, from resume text)
    signals["linkedin"] = extract_linkedin_signals_from_resume(resume_text)

    # Certifications (synchronous detection from resume)
    detected_certs = detect_certifications(resume_text)
    signals["certifications"] = detected_certs

    return signals


# ─────────────────────────────────────────────────────────────
# External signal scoring
# ─────────────────────────────────────────────────────────────


def _score_external_signals(
    external_signals: dict[str, Any],
    claimed_skills: list[str],
    role_type: str,
) -> dict[str, float]:
    """Score all external signals into 0.0–1.0 range."""
    scores: dict[str, float] = {}

    # GitHub
    gh_data = external_signals.get("github", {})
    scores["github_score"] = score_github(gh_data) if gh_data else 0.0

    # Competitive coding
    cf_data = external_signals.get("codeforces", {})
    cc_data = external_signals.get("codechef", {})
    lc_data = external_signals.get("leetcode", {})
    scores["competitive_coding"] = score_competitive_coding(
        cf_data,
        cc_data,
        lc_data,
    )

    # Portfolio
    portfolio_data = external_signals.get("portfolio", {})
    scores["portfolio_score"] = score_portfolio(portfolio_data, claimed_skills)

    # LinkedIn
    linkedin_data = external_signals.get("linkedin", {})
    scores["linkedin_score"] = score_linkedin(linkedin_data, role_type)

    # Certifications
    cert_data = external_signals.get("certifications", [])
    scores["certification_score"] = score_certifications(
        cert_data,
        claimed_skills,
    )

    # Placeholder scores for signals not yet implemented
    scores["stackoverflow_score"] = 0.0
    scores["research_score"] = 0.0
    scores["live_test_score"] = 0.0
    scores["video_score"] = 0.0
    scores["reference_score"] = 0.0

    return scores


# ─────────────────────────────────────────────────────────────
# Score fusion with role weights
# ─────────────────────────────────────────────────────────────


def _build_component_breakdown(
    all_scores: dict[str, float],
    role_weights: dict[str, float],
) -> dict[str, dict[str, float]]:
    """
    Build detailed component breakdown with raw and weighted scores.

    Returns dict mapping signal name → {raw_score, weight, weighted_score}.
    """
    breakdown: dict[str, dict[str, float]] = {}

    for signal_key, weight in role_weights.items():
        raw_score = all_scores.get(signal_key, 0.0)
        weighted = round(raw_score * weight, 6)
        breakdown[signal_key] = {
            "raw_score": round(raw_score, 4),
            "weight": weight,
            "weighted_score": weighted,
        }

    return breakdown


# ─────────────────────────────────────────────────────────────
# Recommendation engine
# ─────────────────────────────────────────────────────────────


def generate_recommendations(
    missing_skills: list[str] | None = None,
    low_scores: dict[str, float] | None = None,
    trust_result: dict[str, Any] | None = None,
    external_signals: dict[str, Any] | None = None,
) -> list[str]:
    """
    Generate 3–5 actionable recommendations for the candidate.

    Args:
        missing_skills:   Skills required by JD but not on resume.
        low_scores:       Signal names with scores below threshold.
        trust_result:     Trust verification result dict.
        external_signals: All fetched external signals.

    Returns:
        List of actionable recommendation strings.
    """
    recs: list[str] = []

    missing_skills = missing_skills or []
    low_scores = low_scores or {}
    trust_result = trust_result or {}
    external_signals = external_signals or {}

    # ─── Missing skill recommendations ───
    if missing_skills:
        top_missing = missing_skills[:3]
        recs.append(
            f"Strengthen profile by learning: {', '.join(top_missing)}. "
            f"Consider adding projects or certifications in these areas."
        )

    # ─── Low GitHub score ───
    if low_scores.get("github_score", 1.0) < 0.4:
        github_data = external_signals.get("github", {})
        if not github_data:
            recs.append(
                "Create a GitHub profile with public repositories showcasing "
                "your skills. Aim for consistent commit history and well-documented projects."
            )
        else:
            recs.append(
                "Improve GitHub presence: add READMEs to repos, write tests, "
                "and contribute to open-source projects to demonstrate collaboration."
            )

    # ─── Low competitive coding score ───
    if low_scores.get("competitive_coding", 1.0) < 0.4:
        recs.append(
            "Practice competitive programming on LeetCode, Codeforces, or CodeChef. "
            "Solving 200+ problems significantly strengthens your profile."
        )

    # ─── Low portfolio score ───
    if low_scores.get("portfolio_score", 1.0) < 0.4:
        recs.append(
            "Build a portfolio website showcasing 3–5 projects with live demos. "
            "Use a custom domain and include links to source code."
        )

    # ─── Certification gaps ───
    if low_scores.get("certification_score", 1.0) < 0.3:
        cert_recommendations = {
            "backend_engineer": "AWS Solutions Architect Associate or Google Cloud Professional",
            "frontend_engineer": "Meta Front-End Developer Certificate or AWS Cloud Practitioner",
            "devops_engineer": "AWS DevOps Professional or Certified Kubernetes Administrator (CKA)",
            "data_engineer": "Google Professional Data Engineer or AWS Data Analytics Specialty",
            "ml_engineer": "TensorFlow Developer Certificate or AWS Machine Learning Specialty",
        }
        cert_rec = cert_recommendations.get(
            "backend_engineer",
            "a relevant cloud or platform certification",
        )
        recs.append(
            f"Obtain {cert_rec} to validate your expertise. "
            f"Industry certifications add measurable credibility."
        )

    # ─── Trust issues ───
    if trust_result.get("trust_score", 1.0) < 0.7:
        flags = trust_result.get("flags", [])
        high_flags = [f for f in flags if f.get("severity") == "high"]
        if high_flags:
            recs.append(
                "Address verification concerns: ensure all certifications are "
                "current, and that your experience timeline is consistent across "
                "your resume, LinkedIn, and GitHub profiles."
            )

    # ─── LinkedIn presence ───
    linkedin = external_signals.get("linkedin", {})
    if not linkedin.get("has_linkedin", False):
        recs.append(
            "Add your LinkedIn profile URL to your resume. "
            "A complete LinkedIn profile with recommendations boosts credibility."
        )

    # Ensure 3–5 recommendations
    if len(recs) < 3:
        filler_recs = [
            "Keep your resume updated with quantifiable achievements and impact metrics.",
            "Engage in open-source contributions to demonstrate collaboration skills.",
            "Document your projects with clear READMEs, architecture diagrams, and demo links.",
            "Build a personal brand by writing technical blog posts or speaking at meetups.",
        ]
        for fr in filler_recs:
            if fr not in recs and len(recs) < 3:
                recs.append(fr)

    return recs[:5]
