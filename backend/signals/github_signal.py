"""
GitHub Signal Fetcher — Async GitHub profile analysis.

Fetches public GitHub data to evaluate a candidate's open-source activity,
code quality indicators, and language breadth.

All network calls use httpx with a 10-second timeout.
Missing/private profiles return empty dicts — never crash.

Endpoints used:
    GET /users/{username}
    GET /users/{username}/repos?per_page=100&sort=updated
    GET /users/{username}/events?per_page=100
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
TIMEOUT = 10.0


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
        logger.warning(f"GitHub API {resp.status_code} for {url}")
        return None
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"GitHub fetch failed for {url}: {e}")
        return None


async def fetch_github_signals(username: str) -> dict[str, Any]:
    """
    Fetch comprehensive GitHub signals for a user.

    Queries three endpoints (profile, repos, events) concurrently and
    aggregates into a normalized signal dict.

    Args:
        username: GitHub username (e.g., "torvalds").

    Returns:
        Dict with keys:
            account_age_years, total_repos, original_repos, total_stars,
            languages, contribution_streak_estimate, commit_frequency_per_week,
            has_readme_ratio, has_tests, top_repo_stars, open_source_prs_estimate,
            profile_completeness, raw_bio
        Returns empty dict if username is empty or all requests fail.
    """
    if not username or not username.strip():
        return {}

    username = username.strip().lstrip("@")

    async with httpx.AsyncClient() as client:
        # Fetch all three endpoints
        profile_data = await _safe_get(
            client, f"{GITHUB_API_BASE}/users/{username}"
        )
        repos_data = await _safe_get(
            client, f"{GITHUB_API_BASE}/users/{username}/repos?per_page=100&sort=updated"
        )
        events_data = await _safe_get(
            client, f"{GITHUB_API_BASE}/users/{username}/events?per_page=100"
        )

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
    hireable = profile_data.get("hireable")
    followers = profile_data.get("followers", 0)
    public_repos_count = profile_data.get("public_repos", 0)

    # Profile completeness (0-1)
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

        # Check for README via has_pages or description presence
        if repo.get("description") or repo.get("has_pages"):
            readme_count += 1

        # Heuristic for tests: check repo topics or name patterns
        topics = repo.get("topics", []) or []
        repo_name = (repo.get("name") or "").lower()
        if any(t in ("testing", "test", "tests", "ci", "tdd") for t in topics):
            has_tests_detected = True
        if "test" in repo_name:
            has_tests_detected = True

    has_readme_ratio = round(readme_count / max(len(repos), 1), 2)

    # --- Parse events (commit frequency) ---
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

    # Estimate weekly commit frequency (90 days ≈ 12.86 weeks)
    commit_frequency_per_week = round(commit_count_90d / 12.86, 1)

    # Streak estimate: push events spread across weeks
    contribution_streak_estimate = min(push_event_count, 12)  # cap at 12 weeks

    # PR estimate from PullRequestEvent count
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
    }


def score_github(signals: dict[str, Any], role_type: str = "backend") -> float:
    """
    Compute a normalized GitHub score (0.0–1.0).

    Weights:
        commit_frequency  — 30%
        languages_match   — 25%
        stars             — 20%
        account_age       — 15%
        has_tests         — 10%

    Args:
        signals:   Dict returned by fetch_github_signals().
        role_type: Role to evaluate against (affects language matching).

    Returns:
        Normalized score from 0.0 to 1.0.
    """
    if not signals:
        return 0.0

    # --- Commit Frequency Score (30%) ---
    freq = signals.get("commit_frequency_per_week", 0.0)
    # Scale: 0 commits/week = 0, 10+ commits/week = 1.0
    freq_score = min(freq / 10.0, 1.0)

    # --- Languages Match Score (25%) ---
    candidate_langs = {l.lower() for l in signals.get("languages", [])}
    role_languages = _get_role_languages(role_type)
    if role_languages:
        matched = len(candidate_langs & role_languages)
        lang_score = min(matched / max(len(role_languages) * 0.5, 1), 1.0)
    else:
        # More languages = better if no role-specific check
        lang_score = min(len(candidate_langs) / 5.0, 1.0)

    # --- Stars Score (20%) ---
    stars = signals.get("total_stars", 0)
    # Scale: 0 stars = 0, 100+ total stars = 1.0
    stars_score = min(stars / 100.0, 1.0)

    # --- Account Age Score (15%) ---
    age = signals.get("account_age_years", 0.0)
    # Scale: 0 years = 0, 5+ years = 1.0
    age_score = min(age / 5.0, 1.0)

    # --- Has Tests Score (10%) ---
    tests_score = 1.0 if signals.get("has_tests", False) else 0.0

    # Weighted combination
    total = (
        freq_score * 0.30
        + lang_score * 0.25
        + stars_score * 0.20
        + age_score * 0.15
        + tests_score * 0.10
    )

    # Bonus modifiers (additive, capped at 1.0)
    completeness = signals.get("profile_completeness", 0.0)
    if completeness >= 0.8:
        total += 0.03
    if signals.get("open_source_prs_estimate", 0) >= 5:
        total += 0.02
    if signals.get("has_readme_ratio", 0.0) >= 0.7:
        total += 0.02

    return round(min(max(total, 0.0), 1.0), 4)


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
        "fresher": set(),  # no specific expectation
    }
    return role_map.get(role_type.lower().replace(" ", "_"), set())
