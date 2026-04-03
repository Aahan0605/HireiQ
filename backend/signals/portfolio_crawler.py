"""
Portfolio Crawler — Async website analysis for candidate portfolios.

Fetches a candidate's portfolio URL, parses HTML with BeautifulSoup,
and extracts tech stack mentions, project count, live demos, blog
presence, GitHub links, and load time.

All network calls use httpx with 10-second timeout.
Returns empty dict on failure — never crash.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 10.0

# Tech keywords to scan for in portfolio text (lowercased for matching)
TECH_KEYWORDS: list[str] = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala",
    "react", "angular", "vue", "svelte", "next.js", "nuxt",
    "node.js", "express", "fastapi", "django", "flask", "spring boot",
    "rails", "laravel", "asp.net", "nestjs",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "neo4j", "firebase", "supabase",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
    "jenkins", "github actions", "circleci", "gitlab ci",
    "tensorflow", "pytorch", "scikit-learn", "keras", "pandas", "numpy",
    "spark", "hadoop", "kafka", "airflow",
    "graphql", "rest", "grpc", "websocket", "microservices", "serverless",
    "tailwind", "sass", "css", "html",
    "git", "linux", "nginx", "ci/cd", "agile",
]

# Patterns for blog sections
BLOG_PATTERNS = re.compile(
    r'/blog|/articles?|/posts?|/writing|/thoughts|/journal|/notes',
    re.I,
)

# Patterns for project sections in HTML
PROJECT_SECTION_PATTERNS = [
    re.compile(r'class\s*=\s*["\'][^"\']*project[^"\']*["\']', re.I),
    re.compile(r'class\s*=\s*["\'][^"\']*portfolio[^"\']*["\']', re.I),
    re.compile(r'class\s*=\s*["\'][^"\']*work[^"\']*["\']', re.I),
    re.compile(r'class\s*=\s*["\'][^"\']*card[^"\']*["\']', re.I),
    re.compile(r'id\s*=\s*["\']projects?["\']', re.I),
]

# Email/phone patterns
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'[\+]?[\d\s\-\(\)]{10,15}')

# GitHub URL pattern
GITHUB_LINK_PATTERN = re.compile(
    r'https?://(?:www\.)?github\.com/([a-zA-Z0-9\-]+)(?:/([a-zA-Z0-9\-_.]+))?',
    re.I,
)


async def crawl_portfolio(url: str) -> dict[str, Any]:
    """
    Crawl and analyze a candidate's portfolio website.

    Fetches the page, measures load time, and extracts structured
    signals using BeautifulSoup HTML parsing.

    Args:
        url: Portfolio URL (e.g., "https://janedoe.dev").

    Returns:
        Dict with keys:
            - tech_stack_mentioned: list[str] — matching tech keywords
            - project_count: int — estimated number of project sections
            - has_live_demos: bool — external app links found
            - has_blog: bool — blog/articles section detected
            - github_links: list[str] — GitHub profile/repo URLs
            - last_modified: str | None — from HTTP headers
            - load_time_ms: float — page fetch time in milliseconds
            - contact_info: bool — email or phone detected
            - page_title: str — HTML <title> content
            - meta_description: str — meta description content
            - total_links: int — total <a> tags found
            - total_images: int — total <img> tags found
        Returns empty dict if URL is invalid or fetch fails.

    Examples:
        >>> import asyncio
        >>> result = asyncio.run(crawl_portfolio("https://example.com"))
        >>> isinstance(result, dict)
        True
    """
    if not url or not url.strip():
        return {}

    url = url.strip()

    # Ensure URL has a scheme
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    # Validate URL format
    parsed = urlparse(url)
    if not parsed.netloc:
        logger.warning(f"Invalid portfolio URL: {url}")
        return {}

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("beautifulsoup4 required for portfolio crawling")
        return {}

    # Fetch the page with timing
    html = ""
    load_time_ms = 0.0
    last_modified = None
    headers: dict[str, str] = {}

    try:
        async with httpx.AsyncClient() as client:
            start_time = time.monotonic()
            resp = await client.get(
                url,
                timeout=TIMEOUT,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; HireIQ-Crawler/1.0; "
                        "+https://hireiq.dev/bot)"
                    ),
                },
                follow_redirects=True,
            )
            end_time = time.monotonic()

            load_time_ms = round((end_time - start_time) * 1000, 1)

            if resp.status_code != 200:
                logger.warning(f"Portfolio returned {resp.status_code}: {url}")
                return {}

            html = resp.text
            last_modified = resp.headers.get("last-modified")

    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"Portfolio fetch failed for {url}: {e}")
        return {}

    if not html:
        return {}

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator=" ", strip=True).lower()

    # --- Tech Stack Detection ---
    tech_found: list[str] = []
    for tech in TECH_KEYWORDS:
        # Use word-boundary-aware search for short terms
        if len(tech) <= 3:
            pattern = re.compile(r'\b' + re.escape(tech) + r'\b', re.I)
            if pattern.search(page_text):
                tech_found.append(tech)
        else:
            if tech in page_text:
                tech_found.append(tech)

    # Deduplicate maintaining order
    tech_stack = list(dict.fromkeys(tech_found))

    # --- Project Count ---
    project_count = _count_projects(soup, html)

    # --- Live Demos ---
    has_live_demos = _detect_live_demos(soup, parsed.netloc)

    # --- Blog ---
    all_links = soup.find_all("a", href=True)
    has_blog = any(BLOG_PATTERNS.search(a["href"]) for a in all_links)

    # Also check nav/header text
    nav_text = ""
    for nav in soup.find_all(["nav", "header"]):
        nav_text += nav.get_text(separator=" ", strip=True).lower()
    if any(kw in nav_text for kw in ("blog", "articles", "writing", "posts")):
        has_blog = True

    # --- GitHub Links ---
    github_links: list[str] = []
    seen_gh: set[str] = set()
    for a in all_links:
        gh_match = GITHUB_LINK_PATTERN.match(a["href"])
        if gh_match:
            gh_url = gh_match.group(0)
            if gh_url not in seen_gh:
                seen_gh.add(gh_url)
                github_links.append(gh_url)

    # --- Contact Info ---
    has_email = bool(EMAIL_PATTERN.search(page_text))
    has_phone = bool(PHONE_PATTERN.search(page_text))
    contact_info = has_email or has_phone

    # --- Page Meta ---
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else ""

    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc.get("content", "") if meta_desc else ""

    # --- Counts ---
    total_links = len(all_links)
    total_images = len(soup.find_all("img"))

    return {
        "tech_stack_mentioned": tech_stack,
        "project_count": project_count,
        "has_live_demos": has_live_demos,
        "has_blog": has_blog,
        "github_links": github_links,
        "last_modified": last_modified,
        "load_time_ms": load_time_ms,
        "contact_info": contact_info,
        "page_title": page_title,
        "meta_description": meta_description,
        "total_links": total_links,
        "total_images": total_images,
    }


def _count_projects(soup: Any, html: str) -> int:
    """
    Estimate the number of projects showcased on the portfolio.

    Uses multiple heuristics:
        1. Elements with class containing 'project', 'portfolio', 'work'
        2. <article> or <section> tags within project containers
        3. Cards (class containing 'card') in main content
    """
    count = 0

    # Strategy 1: Direct project-class elements
    for selector in [
        "[class*='project']",
        "[class*='portfolio-item']",
        "[class*='work-item']",
    ]:
        elements = soup.select(selector)
        if elements:
            count = max(count, len(elements))

    # Strategy 2: Count cards/articles in project sections
    for section in soup.find_all(["section", "div"], id=re.compile(r"project", re.I)):
        cards = section.find_all(["article", "div"], class_=re.compile(r"card|item", re.I))
        if cards:
            count = max(count, len(cards))

    # Strategy 3: Count via project section pattern matches in raw HTML
    if count == 0:
        for pattern in PROJECT_SECTION_PATTERNS:
            matches = pattern.findall(html)
            count = max(count, len(matches))

    # Strategy 4: Fallback — count <h3> or <h2> tags that might be project titles
    if count == 0:
        project_headings = soup.find_all(
            ["h2", "h3"],
            string=re.compile(r"project|built|created|developed", re.I),
        )
        count = len(project_headings)

    return count


def _detect_live_demos(soup: Any, portfolio_domain: str) -> bool:
    """
    Detect if the portfolio links to live demo applications.

    Looks for external HTTP links that are NOT:
        - The portfolio's own domain
        - Common social/profile links (github, linkedin, twitter, etc.)
        - CDN/resource links
    """
    excluded_domains = {
        "github.com", "linkedin.com", "twitter.com", "x.com",
        "facebook.com", "instagram.com", "youtube.com",
        "medium.com", "dev.to", "stackoverflow.com",
        "fonts.googleapis.com", "cdn.jsdelivr.net", "unpkg.com",
        "cdnjs.cloudflare.com", "fonts.gstatic.com",
        portfolio_domain.lower(),
    }

    demo_keywords = {"demo", "live", "app", "deploy", "hosted", "visit", "try"}

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith(("http://", "https://")):
            continue

        parsed = urlparse(href)
        domain = parsed.netloc.lower().lstrip("www.")

        if domain in excluded_domains:
            continue

        # Check if link text suggests a demo
        link_text = a.get_text(strip=True).lower()
        if any(kw in link_text for kw in demo_keywords):
            return True

        # Check if it's a deployed app domain (common patterns)
        app_domains = [
            ".vercel.app", ".netlify.app", ".herokuapp.com",
            ".surge.sh", ".github.io", ".pages.dev",
            ".fly.dev", ".railway.app", ".render.com",
        ]
        if any(domain.endswith(d) for d in app_domains):
            return True

    return False


def score_portfolio(
    signals: dict[str, Any],
    jd_required_skills: list[str],
) -> float:
    """
    Score a portfolio based on crawl signals.

    Weights:
        tech_match       — 40%  (overlap between portfolio tech and JD skills)
        has_live_demos   — 25%  (demonstrates deployment ability)
        project_count    — 20%  (normalized: 5+ projects = 1.0)
        recency          — 15%  (based on last-modified header)

    Args:
        signals:             Dict returned by crawl_portfolio().
        jd_required_skills:  List of required skill names from JD.

    Returns:
        Normalized score from 0.0 to 1.0.
    """
    if not signals:
        return 0.0

    # --- Tech Match Score (40%) ---
    portfolio_tech = {t.lower() for t in signals.get("tech_stack_mentioned", [])}
    required_lower = {s.lower() for s in jd_required_skills} if jd_required_skills else set()

    if required_lower:
        matched = len(portfolio_tech & required_lower)
        tech_score = min(matched / max(len(required_lower) * 0.5, 1), 1.0)
    else:
        # No specific requirements — reward breadth
        tech_score = min(len(portfolio_tech) / 8.0, 1.0)

    # --- Live Demos Score (25%) ---
    demo_score = 1.0 if signals.get("has_live_demos", False) else 0.0

    # --- Project Count Score (20%) ---
    project_count = signals.get("project_count", 0)
    project_score = min(project_count / 5.0, 1.0)

    # --- Recency Score (15%) ---
    recency_score = _compute_recency_score(signals.get("last_modified"))

    # Weighted combination
    total = (
        tech_score * 0.40
        + demo_score * 0.25
        + project_score * 0.20
        + recency_score * 0.15
    )

    # Bonus modifiers
    if signals.get("has_blog", False):
        total += 0.05  # writing/knowledge sharing
    if signals.get("contact_info", False):
        total += 0.02  # professionalism
    if signals.get("github_links"):
        total += 0.02  # open source integration
    if signals.get("load_time_ms", 10000) < 2000:
        total += 0.02  # performance awareness

    return round(min(max(total, 0.0), 1.0), 4)


def _compute_recency_score(last_modified: Optional[str]) -> float:
    """
    Compute recency score from the Last-Modified header.

    Returns:
        1.0 if modified within last 3 months,
        0.7 if within last 6 months,
        0.4 if within last year,
        0.2 if older,
        0.5 if no header (assume moderate recency).
    """
    if not last_modified:
        return 0.5  # Unknown — give neutral score

    from datetime import datetime, timezone
    from email.utils import parsedate_to_datetime

    try:
        modified_dt = parsedate_to_datetime(last_modified)
        now = datetime.now(timezone.utc)
        days_ago = (now - modified_dt).days

        if days_ago <= 90:
            return 1.0
        elif days_ago <= 180:
            return 0.7
        elif days_ago <= 365:
            return 0.4
        else:
            return 0.2
    except (ValueError, TypeError):
        return 0.5
