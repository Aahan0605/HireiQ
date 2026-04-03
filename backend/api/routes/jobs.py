"""
Jobs Router — Endpoints for job description parsing and role profiles.

Routes:
    POST /jobs/parse-jd           — Parse raw JD text into structured features
    GET  /jobs/role-profiles      — List all available role weight profiles
    POST /jobs/role-profiles/custom — Submit and validate a custom weight profile
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from api.models import (
    CustomRoleProfile,
    JDParseRequest,
    JDParseResponse,
)
from config import ROLE_WEIGHT_PROFILES, SCORING_WEIGHTS
from parser.feature_extractor import extract_features

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])

# ─────────────────────────────────────────────────────────────
# Role type detection keywords
# ─────────────────────────────────────────────────────────────
_ROLE_KEYWORDS: dict[str, list[str]] = {
    "frontend_engineer": [
        "react", "angular", "vue", "svelte", "css", "html", "frontend",
        "front-end", "ui developer", "web developer", "javascript developer",
    ],
    "backend_engineer": [
        "backend", "back-end", "api", "server-side", "microservices",
        "java developer", "python developer", "golang", "node.js developer",
    ],
    "fullstack_engineer": [
        "fullstack", "full-stack", "full stack",
    ],
    "devops_engineer": [
        "devops", "sre", "site reliability", "infrastructure",
        "platform engineer", "cloud engineer", "kubernetes", "terraform",
    ],
    "data_engineer": [
        "data engineer", "etl", "data pipeline", "spark", "airflow",
        "data warehouse", "bigquery", "redshift",
    ],
    "ml_engineer": [
        "machine learning", "deep learning", "ml engineer", "ai engineer",
        "nlp", "computer vision", "tensorflow", "pytorch",
    ],
    "mobile_developer": [
        "android", "ios", "react native", "flutter", "mobile developer",
        "swift developer", "kotlin developer",
    ],
}

# Common skills for extraction
_SKILL_PATTERNS: list[str] = [
    "python", "java", "javascript", "typescript", "go", "golang", "rust",
    "c\\+\\+", "c#", "ruby", "php", "swift", "kotlin", "scala", "r",
    "react", "angular", "vue", "svelte", "next\\.js", "nuxt",
    "node\\.js", "express", "fastapi", "django", "flask", "spring",
    "rails", "laravel", "asp\\.net", "nestjs",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "graphql", "rest", "grpc", "kafka", "rabbitmq",
    "git", "ci/cd", "jenkins", "github actions",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "pandas", "spark", "airflow", "dbt",
    "html", "css", "tailwind", "sass",
    "linux", "bash", "sql", "nosql",
    "agile", "scrum", "jira",
]


# ─────────────────────────────────────────────────────────────
# POST /jobs/parse-jd
# ─────────────────────────────────────────────────────────────

@router.post("/parse-jd", response_model=JDParseResponse)
async def parse_job_description(request: JDParseRequest) -> JDParseResponse:
    """
    Parse raw job description text into structured features.

    Extracts required skills, experience requirements, education level,
    suggested role type, and keyword list.
    """
    text = request.text
    text_lower = text.lower()

    # ─── Extract skills ───
    required_skills: list[str] = []
    preferred_skills: list[str] = []

    for pattern in _SKILL_PATTERNS:
        if re.search(r'\b' + pattern + r'\b', text_lower):
            skill = pattern.replace("\\", "").replace(".", ".")
            # Classify based on context
            # Look for "required", "must have" near the skill
            skill_pos = text_lower.find(skill.lower())
            context_before = text_lower[max(0, skill_pos - 100):skill_pos]

            if any(w in context_before for w in ["required", "must", "essential", "mandatory"]):
                required_skills.append(skill)
            elif any(w in context_before for w in ["preferred", "nice to have", "bonus", "plus"]):
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)  # default to required

    # Deduplicate
    required_skills = sorted(set(required_skills))
    preferred_skills = sorted(set(preferred_skills) - set(required_skills))

    # ─── Extract experience ───
    exp_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
        r'(?:experience|exp)\s*[:\-]?\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(?:minimum|min|at\s+least)\s*(\d+)\s*(?:years?|yrs?)',
    ]
    experience_required = 0.0
    for pattern in exp_patterns:
        match = re.search(pattern, text_lower)
        if match:
            experience_required = float(match.group(1))
            break

    # ─── Extract education ───
    edu_keywords = {
        "phd": "Ph.D.",
        "doctorate": "Ph.D.",
        "master": "Master's",
        "bachelor": "Bachelor's",
        "associate": "Associate's",
        "diploma": "Diploma",
    }
    education_required = "Not specified"
    for keyword, label in edu_keywords.items():
        if keyword in text_lower:
            education_required = label
            break

    # ─── Detect role type ───
    if request.role_hint and request.role_hint in ROLE_WEIGHT_PROFILES:
        suggested_role_type = request.role_hint
    else:
        suggested_role_type = _detect_role_type(text_lower)

    # ─── Build keyword list ───
    # Extract all meaningful keywords (nouns, technical terms)
    all_keywords = required_skills + preferred_skills
    # Add additional keywords from text
    extra_keywords = _extract_keywords(text_lower)
    keyword_list = sorted(set(all_keywords + extra_keywords))

    return JDParseResponse(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        experience_required=experience_required,
        education_required=education_required,
        suggested_role_type=suggested_role_type,
        keyword_list=keyword_list[:30],  # Cap at 30
    )


# ─────────────────────────────────────────────────────────────
# GET /jobs/role-profiles
# ─────────────────────────────────────────────────────────────

@router.get("/role-profiles")
async def get_role_profiles() -> dict[str, Any]:
    """
    Return all available role weight profiles with descriptions.
    """
    profiles: dict[str, Any] = {}

    role_descriptions = {
        "backend_engineer": "Server-side development with APIs, databases, and system design",
        "frontend_engineer": "Client-side development with modern UI frameworks",
        "fullstack_engineer": "End-to-end development across frontend and backend",
        "devops_engineer": "Infrastructure, CI/CD, cloud platforms, and reliability",
        "data_engineer": "Data pipelines, warehousing, ETL, and analytics infrastructure",
        "ml_engineer": "Machine learning models, training pipelines, and AI systems",
        "mobile_developer": "Native and cross-platform mobile application development",
    }

    for role_key, weights in ROLE_WEIGHT_PROFILES.items():
        profiles[role_key] = {
            "description": role_descriptions.get(
                role_key,
                f"Custom profile: {role_key}",
            ),
            "weights": weights,
            "weight_sum": round(sum(weights.values()), 4),
            "top_signals": sorted(
                weights.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    return {
        "available_profiles": list(profiles.keys()),
        "profiles": profiles,
        "default_weights": SCORING_WEIGHTS,
    }


# ─────────────────────────────────────────────────────────────
# POST /jobs/role-profiles/custom
# ─────────────────────────────────────────────────────────────

@router.post("/role-profiles/custom")
async def create_custom_profile(
    profile: CustomRoleProfile,
) -> dict[str, Any]:
    """
    Validate and return a custom weight profile.

    Weights must sum to approximately 1.0 (±0.02 tolerance).
    """
    weights = profile.weights
    weight_sum = sum(weights.values())

    # Validate weight sum
    if abs(weight_sum - 1.0) > 0.02:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Weights must sum to ~1.0 (±0.02 tolerance). "
                f"Current sum: {weight_sum:.4f}. "
                f"Delta: {abs(weight_sum - 1.0):.4f}"
            ),
        )

    # Validate all weights are positive
    negative = {k: v for k, v in weights.items() if v < 0}
    if negative:
        raise HTTPException(
            status_code=422,
            detail=f"All weights must be non-negative. Found: {negative}",
        )

    # Validate known signal keys
    valid_keys = set(SCORING_WEIGHTS.keys())
    unknown = set(weights.keys()) - valid_keys
    if unknown:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown signal keys: {', '.join(unknown)}. "
                f"Valid keys: {', '.join(sorted(valid_keys))}"
            ),
        )

    return {
        "status": "valid",
        "profile_name": profile.profile_name,
        "description": profile.description,
        "weights": weights,
        "weight_sum": round(weight_sum, 4),
        "top_signals": sorted(
            weights.items(), key=lambda x: x[1], reverse=True
        )[:5],
    }


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _detect_role_type(text: str) -> str:
    """Detect the most likely role type from JD text."""
    scores: dict[str, int] = {}
    for role, keywords in _ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[role] = score

    if not scores:
        return "backend_engineer"  # default

    return max(scores, key=scores.get)  # type: ignore[arg-type]


def _extract_keywords(text: str) -> list[str]:
    """Extract additional meaningful keywords from JD text."""
    # Technical term patterns
    keyword_patterns = [
        r'\b(?:distributed\s+systems?)\b',
        r'\b(?:system\s+design)\b',
        r'\b(?:data\s+structures?)\b',
        r'\b(?:algorithms?)\b',
        r'\b(?:concurrency)\b',
        r'\b(?:scalability)\b',
        r'\b(?:high\s+availability)\b',
        r'\b(?:load\s+balancing)\b',
        r'\b(?:caching)\b',
        r'\b(?:message\s+queue)\b',
        r'\b(?:event[- ]driven)\b',
        r'\b(?:serverless)\b',
        r'\b(?:containers?)\b',
        r'\b(?:observability)\b',
        r'\b(?:monitoring)\b',
        r'\b(?:security)\b',
        r'\b(?:authentication)\b',
        r'\b(?:authorization)\b',
        r'\b(?:oauth)\b',
        r'\b(?:websocket)\b',
    ]

    keywords: list[str] = []
    for pattern in keyword_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            keywords.append(match.group(0).strip())

    return keywords
