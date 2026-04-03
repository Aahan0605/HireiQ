"""
Pydantic v2 request/response models for HireIQ REST API.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────

class CandidateSubmission(BaseModel):
    """Single candidate submitted for evaluation."""

    name: str = Field(..., min_length=1, max_length=200, description="Candidate full name")
    resume_text: str | None = Field(None, description="Raw resume text (if already extracted)")
    resume_file_path: str | None = Field(None, description="Path to resume file for parsing")
    github_username: str | None = Field(None, max_length=100, description="GitHub username")
    cf_handle: str | None = Field(None, max_length=100, description="Codeforces handle")
    cc_username: str | None = Field(None, max_length=100, description="CodeChef username")
    lc_username: str | None = Field(None, max_length=100, description="LeetCode username")
    portfolio_url: str | None = Field(None, max_length=500, description="Portfolio website URL")


class JobDescription(BaseModel):
    """Job description with extracted requirements."""

    title: str = Field(..., min_length=1, max_length=300, description="Job title")
    description: str = Field(..., min_length=10, description="Full job description text")
    role_type: str = Field("backend_engineer", description="Role profile key from config")
    required_skills: list[str] = Field(default_factory=list, description="Must-have skills")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    experience_required: float = Field(0, ge=0, le=50, description="Minimum years of experience")
    max_experience: float = Field(15, ge=0, le=50, description="Maximum years of experience")


class RankingRequest(BaseModel):
    """Batch ranking request: score and rank multiple candidates against a JD."""

    job: JobDescription
    candidates: list[CandidateSubmission] = Field(..., min_length=1, max_length=500)
    top_k: int = Field(10, ge=1, le=500, description="Number of top candidates to return")
    enable_bias_audit: bool = Field(True, description="Run blind-vs-full bias audit")


class SingleAnalysisRequest(BaseModel):
    """Analyze a single candidate against a JD."""

    candidate: CandidateSubmission
    job: JobDescription


class JDParseRequest(BaseModel):
    """Raw JD text for parsing."""

    text: str = Field(..., min_length=20, description="Job description text to parse")
    role_hint: str | None = Field(None, description="Optional hint for role type detection")


class CustomRoleProfile(BaseModel):
    """Custom weight profile submitted by user."""

    profile_name: str = Field(..., min_length=1, max_length=100)
    weights: dict[str, float] = Field(
        ...,
        description="Signal weights mapping e.g. {'resume_skill_match': 0.20, ...}",
    )
    description: str = Field("", max_length=500)


# ─────────────────────────────────────────────────────────────
# Response models
# ─────────────────────────────────────────────────────────────

class CandidateResult(BaseModel):
    """Full evaluation result for a single candidate."""

    rank: int = Field(..., ge=1)
    name: str
    final_score: float = Field(..., ge=0, le=100)
    trust_score: float = Field(..., ge=0, le=1)
    verdict: str
    component_breakdown: dict
    matched_skills: list[str]
    missing_skills: list[str]
    flags: list[dict]
    recommendations: list[str]
    resume_features: dict | None = None
    external_signals: dict | None = None


class RankingResponse(BaseModel):
    """Response for batch ranking."""

    job_title: str
    role_type: str
    total_candidates: int
    results: list[CandidateResult]
    bias_audit: dict | None = None
    processing_time_ms: float


class ResumeUploadResponse(BaseModel):
    """Response after parsing an uploaded resume."""

    filename: str
    text_length: int
    extracted_text: str
    features: dict


class JDParseResponse(BaseModel):
    """Response after parsing a job description."""

    required_skills: list[str]
    preferred_skills: list[str]
    experience_required: float
    education_required: str
    suggested_role_type: str
    keyword_list: list[str]


class PlatformSignalsResponse(BaseModel):
    """Raw external signal data for a username."""

    username: str
    platforms_queried: list[str]
    signals: dict


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str
    timestamp: str
