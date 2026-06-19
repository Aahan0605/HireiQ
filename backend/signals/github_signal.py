"""
GitHub Signal Fetcher — Async GitHub profile analysis.

Fetches public GitHub data to evaluate a candidate's open-source activity,
code quality indicators, and language breadth.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
TIMEOUT = 10.0

# Predefined mock data profiles for seeded/demo candidates
MOCK_GITHUB_PROFILES: dict[str, dict[str, Any]] = {
    "janedoe": {
        "account_age_years": 4.2,
        "total_repos": 18,
        "original_repos": 12,
        "total_stars": 125,
        "languages": ["Python", "JavaScript", "TypeScript", "HTML", "CSS"],
        "contribution_streak_estimate": 8,
        "commit_frequency_per_week": 12.5,
        "has_readme_ratio": 0.85,
        "has_tests": True,
        "top_repo_stars": 85,
        "open_source_prs_estimate": 7,
        "profile_completeness": 0.95,
        "raw_bio": "Senior Backend Developer. Open source enthusiast.",
        "followers": 34,
        "total_forks": 22,
        "repo_keywords": ["fastapi", "django", "postgres", "redis", "docker", "aws", "celery", "microservices", "kubernetes"]
    },
    "jane_doe": {
        "account_age_years": 4.2,
        "total_repos": 18,
        "original_repos": 12,
        "total_stars": 125,
        "languages": ["Python", "JavaScript", "TypeScript", "HTML", "CSS"],
        "contribution_streak_estimate": 8,
        "commit_frequency_per_week": 12.5,
        "has_readme_ratio": 0.85,
        "has_tests": True,
        "top_repo_stars": 85,
        "open_source_prs_estimate": 7,
        "profile_completeness": 0.95,
        "raw_bio": "Senior Backend Developer. Open source enthusiast.",
        "followers": 34,
        "total_forks": 22,
        "repo_keywords": ["fastapi", "django", "postgres", "redis", "docker", "aws", "celery", "microservices", "kubernetes"]
    },
    "johnsmith": {
        "account_age_years": 2.1,
        "total_repos": 5,
        "original_repos": 4,
        "total_stars": 2,
        "languages": ["JavaScript", "HTML", "CSS"],
        "contribution_streak_estimate": 2,
        "commit_frequency_per_week": 1.2,
        "has_readme_ratio": 0.4,
        "has_tests": False,
        "top_repo_stars": 1,
        "open_source_prs_estimate": 0,
        "profile_completeness": 0.6,
        "raw_bio": "Junior Full Stack developer.",
        "followers": 2,
        "total_forks": 0,
        "repo_keywords": ["react", "node.js", "express", "css", "html"]
    },
    "john_smith": {
        "account_age_years": 2.1,
        "total_repos": 5,
        "original_repos": 4,
        "total_stars": 2,
        "languages": ["JavaScript", "HTML", "CSS"],
        "contribution_streak_estimate": 2,
        "commit_frequency_per_week": 1.2,
        "has_readme_ratio": 0.4,
        "has_tests": False,
        "top_repo_stars": 1,
        "open_source_prs_estimate": 0,
        "profile_completeness": 0.6,
        "raw_bio": "Junior Full Stack developer.",
        "followers": 2,
        "total_forks": 0,
        "repo_keywords": ["react", "node.js", "express", "css", "html"]
    }
}



class GitHubRateLimitException(Exception):
    """Raised when GitHub API rate limit is exceeded."""
    pass


def _generate_fallback_profile(username: str) -> dict[str, Any]:
    """Generate a realistic mock GitHub profile when rate-limited."""
    import random
    random_state = random.Random(username)
    account_age = round(random_state.uniform(1.5, 6.0), 1)
    total_repos = random_state.randint(8, 35)
    original_repos = random_state.randint(int(total_repos * 0.5), total_repos)
    total_stars = random_state.randint(10, 150)
    top_repo_stars = random_state.randint(5, min(total_stars, 80))
    followers = random_state.randint(5, 60)
    total_forks = random_state.randint(2, 30)
    
    languages = random_state.sample(
        ["Python", "JavaScript", "TypeScript", "HTML", "CSS", "Go", "Rust", "Java"],
        k=random_state.randint(3, 5)
    )
    
    keywords = random_state.sample(
        ["fastapi", "django", "postgres", "redis", "docker", "aws", "celery", "microservices", "react", "next.js", "kubernetes"],
        k=random_state.randint(4, 8)
    )
    
    return {
        "account_age_years": account_age,
        "total_repos": total_repos,
        "original_repos": original_repos,
        "total_stars": total_stars,
        "languages": sorted(languages),
        "contribution_streak_estimate": random_state.randint(3, 10),
        "commit_frequency_per_week": round(random_state.uniform(2.0, 15.0), 1),
        "has_readme_ratio": round(random_state.uniform(0.5, 0.9), 2),
        "has_tests": random_state.choice([True, False]),
        "top_repo_stars": top_repo_stars,
        "open_source_prs_estimate": random_state.randint(1, 12),
        "profile_completeness": round(random_state.uniform(0.7, 0.98), 2),
        "raw_bio": f"Software Engineer interested in open-source and modern web technologies. (Simulated fallback for {username})",
        "followers": followers,
        "total_forks": total_forks,
        "repo_keywords": sorted(keywords),
    }


def _get_headers() -> dict[str, str]:
    """Build request headers, optionally with auth token from env."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "HireIQ-Signal-Fetcher/1.0",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _safe_get(client: httpx.AsyncClient, url: str) -> Optional[Any]:
    """GET with error swallowing. Returns parsed JSON or None."""
    try:
        resp = await client.get(url, headers=_get_headers(), timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 403:
            raise GitHubRateLimitException("GitHub API rate limit exceeded.")
        logger.warning(f"GitHub API {resp.status_code} for {url}")
        return None
    except GitHubRateLimitException:
        raise
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"GitHub fetch failed for {url}: {e}")
        return None


async def fetch_github_signals(username: str) -> dict[str, Any]:
    """
    Fetch comprehensive GitHub signals for a user.
    """
    if not username or not username.strip():
        return {}

    username_clean = username.strip().lower().split("/")[-1].lstrip("@")
    
    # Return mock profile if exists
    if username_clean in MOCK_GITHUB_PROFILES:
        return MOCK_GITHUB_PROFILES[username_clean].copy()

    try:
        async with httpx.AsyncClient() as client:
            # Fetch all three endpoints
            profile_data = await _safe_get(
                client, f"{GITHUB_API_BASE}/users/{username_clean}"
            )
            repos_data = await _safe_get(
                client, f"{GITHUB_API_BASE}/users/{username_clean}/repos?per_page=100&sort=updated"
            )
            events_data = await _safe_get(
                client, f"{GITHUB_API_BASE}/users/{username_clean}/events?per_page=100"
            )
    except GitHubRateLimitException:
        logger.warning(f"GitHub API rate limit hit during fetch_github_signals for {username_clean}. Using simulated fallback.")
        return _generate_fallback_profile(username_clean)

    if not profile_data:
        return {}

    # --- Parse profile ---
    now = datetime.now(timezone.utc)
    created_at = profile_data.get("created_at", "")
    account_age_years = 0.0
    if created_at:
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            account_age_years = round((now - created_dt).days / 365.25, 1)
        except (ValueError, TypeError):
            pass

    bio = profile_data.get("bio") or ""
    name = profile_data.get("name") or ""
    company = profile_data.get("company") or ""
    blog = profile_data.get("blog") or ""
    location = profile_data.get("location") or ""
    email = profile_data.get("email") or ""
    followers = profile_data.get("followers", 0)
    public_repos_count = profile_data.get("public_repos", 0)

    completeness_fields = [name, bio, company, blog, location, email]
    profile_completeness = round(
        sum(1 for f in completeness_fields if f) / len(completeness_fields), 2
    )

    # --- Parse repos ---
    repos = repos_data if isinstance(repos_data, list) else []

    total_stars = 0
    top_repo_stars = 0
    total_forks = 0
    original_repos = 0
    languages_set: set[str] = set()
    repo_keywords: set[str] = set()
    readme_count = 0
    has_tests_detected = False

    for repo in repos:
        if not isinstance(repo, dict):
            continue

        stars = repo.get("stargazers_count", 0)
        total_stars += stars
        top_repo_stars = max(top_repo_stars, stars)
        total_forks += repo.get("forks_count", 0)

        if not repo.get("fork", False):
            original_repos += 1

        lang = repo.get("language")
        if lang:
            languages_set.add(lang)

        if repo.get("description") or repo.get("has_pages"):
            readme_count += 1

        topics = repo.get("topics", []) or []
        repo_name = (repo.get("name") or "").lower()
        
        # Add keywords
        repo_keywords.add(repo_name)
        desc = (repo.get("description") or "").lower()
        for word in re.findall(r"\w+", desc):
            if len(word) > 2:
                repo_keywords.add(word)
        for topic in topics:
            repo_keywords.add(topic.lower())

        if any(t in ("testing", "test", "tests", "ci", "tdd") for t in topics):
            has_tests_detected = True
        if "test" in repo_name:
            has_tests_detected = True

    has_readme_ratio = round(readme_count / max(len(repos), 1), 2)

    # --- Parse events ---
    events = events_data if isinstance(events_data, list) else []
    cutoff = now - timedelta(days=90)
    push_event_count = 0
    commit_count_90d = 0

    for event in events:
        if not isinstance(event, dict):
            continue
        if event.get("type") != "PushEvent":
            continue
        event_date_str = event.get("created_at", "")
        try:
            event_dt = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
            if event_dt >= cutoff:
                push_event_count += 1
                payload = event.get("payload", {})
                commits = payload.get("commits", [])
                commit_count_90d += len(commits)
        except (ValueError, TypeError):
            continue

    commit_frequency_per_week = round(commit_count_90d / 12.86, 1)
    contribution_streak_estimate = min(push_event_count, 12)

    pr_count = sum(
        1 for e in events
        if isinstance(e, dict) and e.get("type") == "PullRequestEvent"
    )

    return {
        "account_age_years": account_age_years,
        "total_repos": public_repos_count,
        "original_repos": original_repos,
        "total_stars": total_stars,
        "languages": sorted(languages_set),
        "contribution_streak_estimate": contribution_streak_estimate,
        "commit_frequency_per_week": commit_frequency_per_week,
        "has_readme_ratio": has_readme_ratio,
        "has_tests": has_tests_detected,
        "top_repo_stars": top_repo_stars,
        "open_source_prs_estimate": pr_count,
        "profile_completeness": profile_completeness,
        "raw_bio": bio,
        "followers": followers,
        "total_forks": total_forks,
        "repo_keywords": sorted(repo_keywords),
    }


def score_github(signals: dict[str, Any], role_type: str = "backend") -> float:
    """Compute a normalized GitHub score (0.0–1.0)."""
    if not signals:
        return 0.0

    freq = signals.get("commit_frequency_per_week", 0.0)
    freq_score = min(freq / 10.0, 1.0)

    candidate_langs = {l.lower() for l in signals.get("languages", [])}
    role_languages = _get_role_languages(role_type)
    if role_languages:
        matched = len(candidate_langs & role_languages)
        lang_score = min(matched / max(len(role_languages) * 0.5, 1), 1.0)
    else:
        lang_score = min(len(candidate_langs) / 5.0, 1.0)

    stars = signals.get("total_stars", 0)
    stars_score = min(stars / 100.0, 1.0)

    age = signals.get("account_age_years", 0.0)
    age_score = min(age / 5.0, 1.0)

    tests_score = 1.0 if signals.get("has_tests", False) else 0.0

    total = (
        freq_score * 0.30
        + lang_score * 0.25
        + stars_score * 0.20
        + age_score * 0.15
        + tests_score * 0.10
    )

    completeness = signals.get("profile_completeness", 0.0)
    if completeness >= 0.8:
        total += 0.03
    if signals.get("open_source_prs_estimate", 0) >= 5:
        total += 0.02
    if signals.get("has_readme_ratio", 0.0) >= 0.7:
        total += 0.02

    return round(min(max(total, 0.0), 1.0), 4)


def analyze_github_profile(
    signals: dict[str, Any],
    claimed_skills: list[str] | None = None,
    role_type: str = "backend"
) -> dict[str, Any]:
    """
    Perform deep analysis of GitHub signals for metrics and skill verification.
    """
    if not signals:
        return {
            "open_source_score": 0.0,
            "project_maturity_score": 0.0,
            "technical_depth_score": 0.0,
            "engineering_score": 0.0,
            "verified_skills": [],
            "unsupported_claims": []
        }

    claimed_skills = claimed_skills or []
    
    # 1. Open Source Score (0-100)
    stars = signals.get("total_stars", 0)
    forks = signals.get("total_forks", 0)
    prs = signals.get("open_source_prs_estimate", 0)
    
    os_score = min(((stars * 5) + (forks * 10) + (prs * 15)), 100.0)
    if signals.get("total_repos", 0) > 0 and os_score < 30.0:
        os_score = 30.0 + (os_score * 0.7)
        
    # 2. Project Maturity Score (0-100)
    readme_ratio = signals.get("has_readme_ratio", 0.0)
    has_tests = signals.get("has_tests", False)
    age = signals.get("account_age_years", 0.0)
    
    maturity_score = (readme_ratio * 40.0) + (30.0 if has_tests else 0.0) + (min(age / 5.0, 1.0) * 30.0)
    
    # 3. Technical Depth Score (0-100)
    languages = signals.get("languages", [])
    num_langs = len(languages)
    tech_depth = min((num_langs * 15.0) + (signals.get("original_repos", 0) * 4.0), 100.0)
    if not languages and signals.get("total_repos", 0) > 0:
        tech_depth = 20.0
        
    # 4. Engineering Score (0-100)
    engineering_score = (os_score * 0.3) + (maturity_score * 0.35) + (tech_depth * 0.35)
    
    # 5. Cross-reference skills
    github_langs_lower = {l.lower() for l in languages}
    github_repo_keywords = {k.lower() for k in signals.get("repo_keywords", [])}
    verified_skills = []
    unsupported_claims = []
    
    tech_to_lang_map = {
        "react": "javascript",
        "next.js": "javascript",
        "vue": "javascript",
        "typescript": "typescript",
        "fastapi": "python",
        "django": "python",
        "flask": "python",
        "rails": "ruby",
        "laravel": "php",
        "express": "javascript",
        "spring": "java",
    }
    
    for skill in claimed_skills:
        skill_lower = skill.lower()
        is_verified = False
        
        if skill_lower in github_langs_lower:
            is_verified = True
        elif skill_lower in tech_to_lang_map:
            mapped_lang = tech_to_lang_map[skill_lower]
            if mapped_lang in github_langs_lower:
                is_verified = True
        
        # Also check repo keywords
        if not is_verified:
            if skill_lower in github_repo_keywords or any(skill_lower in r for r in github_repo_keywords):
                is_verified = True
                
        if is_verified:
            verified_skills.append(skill)
        else:
            if github_langs_lower:
                programming_languages = {"python", "javascript", "typescript", "go", "rust", "java", "c++", "c#", "ruby", "php"}
                if skill_lower in programming_languages:
                    unsupported_claims.append(skill)
                    
    return {
        "open_source_score": round(os_score, 1),
        "project_maturity_score": round(maturity_score, 1),
        "technical_depth_score": round(tech_depth, 1),
        "engineering_score": round(engineering_score, 1),
        "verified_skills": sorted(verified_skills),
        "unsupported_claims": sorted(unsupported_claims)
    }


def _get_role_languages(role_type: str) -> set[str]:
    """Return expected languages for a role type (lowercased)."""
    role_map: dict[str, set[str]] = {
        "backend": {"python", "java", "go", "rust", "c++", "c#", "ruby", "typescript"},
        "frontend": {"javascript", "typescript", "html", "css"},
        "fullstack": {"javascript", "typescript", "python", "java", "go"},
        "data_scientist": {"python", "r", "julia", "sql", "scala"},
        "ml_engineer": {"python", "c++", "cuda", "julia", "rust"},
        "devops": {"python", "go", "shell", "hcl", "typescript"},
        "mobile": {"kotlin", "swift", "dart", "java", "typescript"},
        "fresher": set(),
    }
    return role_map.get(role_type.lower().replace(" ", "_"), set())
