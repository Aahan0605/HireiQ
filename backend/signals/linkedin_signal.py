"""
LinkedIn Signal Fetcher — Async LinkedIn profile analysis.

LinkedIn does not provide a free public API for profile data.
This module provides URL validation, resume-text-based extraction,
and a rules-based high-fidelity profile enrichment/simulator.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Predefined mock data profiles for seeded/demo candidates
MOCK_LINKEDIN_PROFILES: dict[str, dict[str, Any]] = {
    "jane_doe": {
        "headline": "Senior Software Engineer @ TechCorp | Cloud Architect",
        "connections": 650,
        "recommendations": 4,
        "endorsements": {"Python": 45, "React": 38, "FastAPI": 24, "AWS": 31},
        "skills": ["Python", "React", "FastAPI", "AWS", "SQL", "PostgreSQL", "Docker", "Kubernetes"],
        "experience": [
            {"title": "Senior Software Engineer", "company": "TechCorp", "duration": "June 2022 - Present", "description": "Led team of 4 to rebuild core data pipelines. Optimized backend API speed by 40%."},
            {"title": "Software Engineer", "company": "WebStart", "duration": "Jan 2020 - May 2022", "description": "Built responsive React/TypeScript frontends."}
        ],
        "education": [
            {"degree": "B.Tech in Computer Science", "school": "IIT Bombay", "duration": "2016 - 2020"}
        ],
        "certifications": ["AWS Certified Solutions Architect", "Certified Kubernetes Administrator"],
        "leadership_indicators": ["Led a team of 4", "Architect"],
        "profile_strength_score": 92.0,
        "career_progression_score": 88.0,
        "industry_relevance_score": 95.0,
    },
    "john_smith": {
        "headline": "Full Stack Developer specializing in React and Node.js",
        "connections": 320,
        "recommendations": 1,
        "endorsements": {"JavaScript": 30, "React": 25, "Node.js": 20},
        "skills": ["JavaScript", "React", "Node.js", "CSS", "HTML", "SQL"],
        "experience": [
            {"title": "Full Stack Developer", "company": "DevStudio", "duration": "Mar 2021 - Present", "description": "Building client websites and web applications."}
        ],
        "education": [
            {"degree": "B.S. in Software Engineering", "school": "State University", "duration": "2017 - 2021"}
        ],
        "certifications": [],
        "leadership_indicators": [],
        "profile_strength_score": 70.0,
        "career_progression_score": 65.0,
        "industry_relevance_score": 75.0,
    }
}

def extract_linkedin_url(text: str) -> str | None:
    """Extract a LinkedIn profile URL from resume text."""
    pattern = re.compile(
        r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-]+)/?',
        re.I,
    )
    match = pattern.search(text)
    return match.group(0).rstrip("/") if match else None

def generate_linkedin_signals(name: str, linkedin_url: str | None, claimed_skills: list[str]) -> dict[str, Any]:
    """
    Generate or retrieve simulated/mock LinkedIn profile data.
    """
    if not name:
        return {"has_linkedin": False}

    normalized_name = name.lower().strip().replace(" ", "_")

    # Match mock profile if exists
    if normalized_name in MOCK_LINKEDIN_PROFILES:
        profile = MOCK_LINKEDIN_PROFILES[normalized_name].copy()
        profile["has_linkedin"] = True
        profile["linkedin_url"] = linkedin_url or f"https://linkedin.com/in/{normalized_name}"
        profile["inconsistencies"] = []
        profile["missing_resume_info"] = []
        if "skills" not in profile:
            profile["skills"] = list(profile.get("endorsements", {}).keys())
        return profile

    has_linkedin = linkedin_url is not None and len(str(linkedin_url).strip()) > 0
    simulated_profile = {
        "has_linkedin": has_linkedin,
        "linkedin_url": linkedin_url,
        "headline": f"Software Specialist | Focus on Technology Solutions",
        "connections": 250,
        "recommendations": 1,
        "endorsements": {"Engineering": 15, "Problem Solving": 10},
        "skills": list(claimed_skills) if has_linkedin else [],
        "experience": [
            {"title": "Software Engineer", "company": "Freelance/Various", "duration": "2021 - Present"}
        ],
        "education": [],
        "certifications": [],
        "leadership_indicators": [],
        "profile_strength_score": 75.0 if has_linkedin else 0.0,
        "career_progression_score": 70.0 if has_linkedin else 0.0,
        "industry_relevance_score": 80.0 if has_linkedin else 0.0,
        "inconsistencies": [],
        "missing_resume_info": []
    }

    if "mismatch" in normalized_name or "fake" in normalized_name:
        simulated_profile["inconsistencies"].append({
            "type": "tenure_mismatch",
            "message": "LinkedIn profile lists 'Lead Engineer' from 2020-2022, but resume states 'Software Engineer' from 2021-2022.",
            "severity": "medium"
        })
        simulated_profile["missing_resume_info"].append(
            "AWS Solutions Architect certification is listed on LinkedIn but missing from Resume."
        )

    return simulated_profile

def extract_linkedin_signals_from_resume(text: str) -> dict[str, Any]:
    """
    Extract LinkedIn-relevant signals from resume text.
    First tries to fetch from seeded mock profiles if candidate's name or handle matches.
    Otherwise, generates simulated/enriched LinkedIn details.
    """
    if not text:
        return {"has_linkedin": False}

    linkedin_url = extract_linkedin_url(text)
    first_lines = [l.strip() for l in text.split("\n") if l.strip()][:3]
    candidate_name = first_lines[0] if first_lines else "unknown"
    
    # Try to extract skills from text to populate simulated profile
    claimed_skills = []
    for s in ["Python", "Java", "Go", "React", "TypeScript", "SQL", "Docker", "Kubernetes", "AWS"]:
        if s.lower() in text.lower():
            claimed_skills.append(s)

    return generate_linkedin_signals(candidate_name, linkedin_url, claimed_skills)

def score_linkedin(signals: dict[str, Any], role_type: str = "backend") -> float:
    """Score LinkedIn signals on a scale of 0.0 - 1.0."""
    if not signals or not signals.get("has_linkedin", False):
        return 0.0

    strength = signals.get("profile_strength_score", 70.0) / 100.0
    progression = signals.get("career_progression_score", 70.0) / 100.0
    relevance = signals.get("industry_relevance_score", 80.0) / 100.0

    # Penalize if there are inconsistencies
    penalty = 0.0
    if signals.get("inconsistencies"):
        penalty = 0.15 * len(signals["inconsistencies"])

    score = 0.4 * strength + 0.3 * progression + 0.3 * relevance - penalty
    return round(min(max(score, 0.0), 1.0), 4)
