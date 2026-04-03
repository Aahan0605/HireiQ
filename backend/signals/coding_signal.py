"""
Competitive Coding Signal Fetcher — Codeforces, CodeChef, LeetCode.

Fetches ratings, solve counts, and problem tags from competitive
programming platforms to evaluate algorithmic proficiency.

All network calls use httpx with 10-second timeout.
Missing/private profiles return empty dicts — never crash.

Endpoints:
    Codeforces: REST API (user.info, user.status)
    CodeChef:   HTML scraping (profile page)
    LeetCode:   GraphQL API (leetcode.com/graphql)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional
from collections import Counter

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 10.0

# ─────────────────────────────────────────────────────────────
# Rating → Normalized Score Tables
# ─────────────────────────────────────────────────────────────
CF_RATING_TABLE: list[tuple[int, float]] = [
    (2400, 1.00),
    (2100, 0.92),
    (1900, 0.82),
    (1600, 0.70),
    (1400, 0.55),
    (1200, 0.40),
    (0,    0.20),
]

CC_RATING_TABLE: list[tuple[int, float]] = [
    (2500, 1.00),
    (2200, 0.90),
    (2000, 0.78),
    (1800, 0.65),
    (1600, 0.50),
    (1400, 0.35),
    (0,    0.15),
]


def _rating_to_score(rating: int, table: list[tuple[int, float]]) -> float:
    """Convert a numeric rating to a 0-1 score using a threshold table."""
    for threshold, score in table:
        if rating >= threshold:
            return score
    return 0.1


# ═══════════════════════════════════════════════════════════════
# Codeforces
# ═══════════════════════════════════════════════════════════════

async def fetch_codeforces(handle: str) -> dict[str, Any]:
    """
    Fetch Codeforces profile and recent submissions.

    Endpoints:
        GET https://codeforces.com/api/user.info?handles={handle}
        GET https://codeforces.com/api/user.status?handle={handle}&count=50

    Args:
        handle: Codeforces username.

    Returns:
        Dict with: rating, max_rating, rank, max_rank, contribution,
                   problems_solved, problem_tags, score (normalized 0-1).
        Empty dict on failure.
    """
    if not handle or not handle.strip():
        return {}

    handle = handle.strip()

    async with httpx.AsyncClient() as client:
        # Fetch user info
        user_data = await _cf_get_user(client, handle)
        if not user_data:
            return {}

        # Fetch recent submissions for problem tags
        submissions = await _cf_get_submissions(client, handle)

    rating = user_data.get("rating", 0)
    max_rating = user_data.get("maxRating", 0)
    rank = user_data.get("rank", "unrated")
    max_rank = user_data.get("maxRank", "unrated")
    contribution = user_data.get("contribution", 0)

    # Analyze solved problems
    solved_problems: set[str] = set()
    tag_counter: Counter = Counter()

    for sub in submissions:
        if not isinstance(sub, dict):
            continue
        verdict = sub.get("verdict")
        problem = sub.get("problem", {})
        if verdict == "OK" and problem:
            problem_id = f"{problem.get('contestId', '')}{problem.get('index', '')}"
            if problem_id and problem_id not in solved_problems:
                solved_problems.add(problem_id)
                for tag in problem.get("tags", []):
                    tag_counter[tag] += 1

    # Top problem tags (skill indicators)
    top_tags = [tag for tag, _ in tag_counter.most_common(10)]

    score = _rating_to_score(max_rating, CF_RATING_TABLE)

    return {
        "platform": "codeforces",
        "rating": rating,
        "max_rating": max_rating,
        "rank": rank,
        "max_rank": max_rank,
        "contribution": contribution,
        "problems_solved": len(solved_problems),
        "problem_tags": top_tags,
        "score": round(score, 4),
    }


async def _cf_get_user(client: httpx.AsyncClient, handle: str) -> Optional[dict]:
    """Fetch Codeforces user info. Returns user dict or None."""
    try:
        resp = await client.get(
            f"https://codeforces.com/api/user.info?handles={handle}",
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "OK" and data.get("result"):
                return data["result"][0]
        return None
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"Codeforces user.info failed for {handle}: {e}")
        return None


async def _cf_get_submissions(client: httpx.AsyncClient, handle: str) -> list[dict]:
    """Fetch recent Codeforces submissions. Returns list or empty."""
    try:
        resp = await client.get(
            f"https://codeforces.com/api/user.status?handle={handle}&count=50",
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "OK":
                return data.get("result", [])
        return []
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"Codeforces user.status failed for {handle}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
# CodeChef
# ═══════════════════════════════════════════════════════════════

async def fetch_codechef(username: str) -> dict[str, Any]:
    """
    Fetch CodeChef profile via HTML scraping.

    Endpoint:
        GET https://www.codechef.com/users/{username}

    Parses the profile page with BeautifulSoup to extract rating,
    stars, and ranking information.

    Args:
        username: CodeChef username.

    Returns:
        Dict with: rating, stars, highest_rating, global_rank,
                   country_rank, problems_solved, score.
        Empty dict on failure.
    """
    if not username or not username.strip():
        return {}

    username = username.strip()

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 required for CodeChef scraping")
        return {}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://www.codechef.com/users/{username}",
                timeout=TIMEOUT,
                headers={"User-Agent": "HireIQ-Signal-Fetcher/1.0"},
                follow_redirects=True,
            )
            if resp.status_code != 200:
                logger.warning(f"CodeChef returned {resp.status_code} for {username}")
                return {}

            html = resp.text
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"CodeChef fetch failed for {username}: {e}")
        return {}

    return _parse_codechef_html(html)


def _parse_codechef_html(html: str) -> dict[str, Any]:
    """Parse CodeChef profile HTML into structured data."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    result: dict[str, Any] = {"platform": "codechef"}

    # Rating
    rating_elem = soup.find("div", class_="rating-number")
    if rating_elem:
        try:
            result["rating"] = int(rating_elem.get_text(strip=True))
        except (ValueError, TypeError):
            result["rating"] = 0
    else:
        result["rating"] = 0

    # Stars (from rating-star span or rating-ranks)
    stars_elem = soup.find("span", class_="rating")
    if stars_elem:
        star_text = stars_elem.get_text(strip=True)
        star_count = star_text.count("★") or star_text.count("⭐")
        if star_count == 0:
            # Try counting from class
            star_match = re.search(r'(\d)', star_text)
            star_count = int(star_match.group(1)) if star_match else 0
        result["stars"] = star_count
    else:
        result["stars"] = 0

    # Highest rating
    highest_elem = soup.find("small", string=re.compile(r"highest", re.I))
    if highest_elem:
        highest_match = re.search(r'(\d+)', highest_elem.get_text())
        result["highest_rating"] = int(highest_match.group(1)) if highest_match else result["rating"]
    else:
        result["highest_rating"] = result["rating"]

    # Rankings — look for global/country rank
    rank_elements = soup.find_all("a", href=re.compile(r"/ratings"))
    result["global_rank"] = 0
    result["country_rank"] = 0
    for elem in rank_elements:
        text = elem.get_text(strip=True)
        rank_match = re.search(r'(\d+)', text)
        if rank_match:
            rank_val = int(rank_match.group(1))
            parent_text = (elem.parent.get_text() if elem.parent else "").lower()
            if "country" in parent_text:
                result["country_rank"] = rank_val
            else:
                result["global_rank"] = rank_val

    # Problems solved
    solved_section = soup.find("section", class_="rating-data-section")
    result["problems_solved"] = 0
    if solved_section:
        solved_match = re.search(r'(\d+)', solved_section.get_text())
        if solved_match:
            result["problems_solved"] = int(solved_match.group(1))

    # Score
    result["score"] = _rating_to_score(result.get("highest_rating", 0), CC_RATING_TABLE)
    result["score"] = round(result["score"], 4)

    return result


# ═══════════════════════════════════════════════════════════════
# LeetCode
# ═══════════════════════════════════════════════════════════════

LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"

LEETCODE_QUERY = """
query getUserProfile($username: String!) {
    matchedUser(username: $username) {
        username
        profile {
            ranking
            realName
            reputation
        }
        submitStatsGlobal {
            acSubmissionNum {
                difficulty
                count
            }
        }
    }
}
"""


async def fetch_leetcode(username: str) -> dict[str, Any]:
    """
    Fetch LeetCode profile via GraphQL API.

    Endpoint:
        POST https://leetcode.com/graphql

    Queries: userPublicProfile + solve statistics.

    Args:
        username: LeetCode username.

    Returns:
        Dict with: total_solved, easy_solved, medium_solved, hard_solved,
                   ranking, reputation, score.
        Empty dict on failure.
    """
    if not username or not username.strip():
        return {}

    username = username.strip()

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                LEETCODE_GRAPHQL_URL,
                json={
                    "query": LEETCODE_QUERY,
                    "variables": {"username": username},
                },
                headers={
                    "Content-Type": "application/json",
                    "Referer": f"https://leetcode.com/{username}/",
                    "User-Agent": "HireIQ-Signal-Fetcher/1.0",
                },
                timeout=TIMEOUT,
            )

            if resp.status_code != 200:
                logger.warning(f"LeetCode returned {resp.status_code} for {username}")
                return {}

            data = resp.json()
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"LeetCode fetch failed for {username}: {e}")
        return {}

    return _parse_leetcode_response(data)


def _parse_leetcode_response(data: dict) -> dict[str, Any]:
    """Parse LeetCode GraphQL response into structured data."""
    try:
        user = data.get("data", {}).get("matchedUser")
        if not user:
            return {}

        profile = user.get("profile", {}) or {}
        stats = user.get("submitStatsGlobal", {}) or {}
        ac_submissions = stats.get("acSubmissionNum", []) or []

        easy = medium = hard = total = 0
        for entry in ac_submissions:
            if not isinstance(entry, dict):
                continue
            diff = (entry.get("difficulty") or "").lower()
            count = entry.get("count", 0)
            if diff == "easy":
                easy = count
            elif diff == "medium":
                medium = count
            elif diff == "hard":
                hard = count
            elif diff == "all":
                total = count

        if total == 0:
            total = easy + medium + hard

        ranking = profile.get("ranking", 0) or 0
        reputation = profile.get("reputation", 0) or 0

        # Score: hard_ratio * 0.5 + medium_ratio * 0.3 + total_normalized * 0.2
        total_for_ratio = max(total, 1)
        hard_ratio = hard / total_for_ratio
        medium_ratio = medium / total_for_ratio

        # Normalize total: 500+ solved = 1.0
        total_normalized = min(total / 500.0, 1.0)

        score = hard_ratio * 0.5 + medium_ratio * 0.3 + total_normalized * 0.2
        score = round(min(max(score, 0.0), 1.0), 4)

        return {
            "platform": "leetcode",
            "total_solved": total,
            "easy_solved": easy,
            "medium_solved": medium,
            "hard_solved": hard,
            "ranking": ranking,
            "reputation": reputation,
            "hard_ratio": round(hard_ratio, 4),
            "medium_ratio": round(medium_ratio, 4),
            "score": score,
        }
    except (KeyError, TypeError, AttributeError) as e:
        logger.warning(f"LeetCode parse error: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
# Unified Scorer
# ═══════════════════════════════════════════════════════════════

def score_competitive_coding(
    cf_data: dict[str, Any],
    cc_data: dict[str, Any],
    lc_data: dict[str, Any],
    role_type: str = "backend",
) -> float:
    """
    Unified competitive coding score from all platforms.

    Computes a weighted average of available platform scores:
        - Codeforces:  35% (algorithmic depth)
        - LeetCode:    40% (interview-relevant)
        - CodeChef:    25% (breadth)

    If a platform has no data, its weight is redistributed proportionally
    to the remaining platforms.

    Args:
        cf_data:   Dict from fetch_codeforces().
        cc_data:   Dict from fetch_codechef().
        lc_data:   Dict from fetch_leetcode().
        role_type: Role type for potential weight adjustments.

    Returns:
        Normalized score from 0.0 to 1.0.
    """
    # Base weights
    weights = {
        "codeforces": 0.35,
        "leetcode":   0.40,
        "codechef":   0.25,
    }

    # Adjust weights for data-heavy roles
    if role_type in ("data_scientist", "ml_engineer"):
        weights["codeforces"] = 0.40  # algorithmic skill matters more
        weights["leetcode"] = 0.35
        weights["codechef"] = 0.25

    scores: dict[str, float] = {}
    if cf_data and cf_data.get("score", 0) > 0:
        scores["codeforces"] = cf_data["score"]
    if lc_data and lc_data.get("score", 0) > 0:
        scores["leetcode"] = lc_data["score"]
    if cc_data and cc_data.get("score", 0) > 0:
        scores["codechef"] = cc_data["score"]

    if not scores:
        return 0.0

    # Redistribute missing platform weights
    active_weight_sum = sum(weights[p] for p in scores)
    if active_weight_sum == 0:
        return 0.0

    total = 0.0
    for platform, score in scores.items():
        normalized_weight = weights[platform] / active_weight_sum
        total += score * normalized_weight

    return round(min(max(total, 0.0), 1.0), 4)
