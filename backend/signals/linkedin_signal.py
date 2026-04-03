"""
LinkedIn Signal Fetcher — Async LinkedIn profile analysis.

LinkedIn does not provide a free public API for profile data.
This module provides:
    1. URL validation and normalization
    2. Resume-text-based LinkedIn signal extraction
    3. Scoring based on extracted LinkedIn-related features

For production use, integrate with LinkedIn's official Marketing/Talent APIs
via OAuth2.0, or use a licensed data provider.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def extract_linkedin_url(text: str) -> str | None:
    """
    Extract a LinkedIn profile URL from resume text.

    Args:
        text: Resume text.

    Returns:
        LinkedIn URL string or None.
    """
    pattern = re.compile(
        r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-]+)/?',
        re.I,
    )
    match = pattern.search(text)
    return match.group(0).rstrip("/") if match else None


def extract_linkedin_signals_from_resume(text: str) -> dict[str, Any]:
    """
    Extract LinkedIn-relevant signals from resume text.

    Since we cannot scrape LinkedIn, we infer signals from what
    candidates mention in their resumes about their LinkedIn presence.

    Args:
        text: Cleaned resume text.

    Returns:
        Dict with: has_linkedin, linkedin_url, recommendations_mentioned,
                   endorsements_mentioned, connections_mentioned,
                   publications_mentioned, volunteer_mentioned.
    """
    if not text:
        return {"has_linkedin": False}

    text_lower = text.lower()

    linkedin_url = extract_linkedin_url(text)

    # Detect LinkedIn-related mentions
    recommendations = bool(re.search(
        r'(\d+)\s*(?:linkedin\s+)?recommendations?', text_lower
    ))
    rec_count = 0
    rec_match = re.search(r'(\d+)\s*(?:linkedin\s+)?recommendations?', text_lower)
    if rec_match:
        rec_count = int(rec_match.group(1))

    endorsements = bool(re.search(
        r'(\d+)\s*(?:skill\s+)?endorsements?', text_lower
    ))

    connections = bool(re.search(
        r'(\d+)\s*\+?\s*(?:linkedin\s+)?connections?', text_lower
    ))
    conn_count = 0
    conn_match = re.search(r'(\d+)\s*\+?\s*connections?', text_lower)
    if conn_match:
        conn_count = int(conn_match.group(1))

    publications = bool(re.search(
        r'publications?|published\s+(?:papers?|articles?)|research\s+papers?',
        text_lower,
    ))

    volunteer = bool(re.search(
        r'volunteer|volunteering|community\s+service|mentoring|mentor',
        text_lower,
    ))

    return {
        "has_linkedin": linkedin_url is not None,
        "linkedin_url": linkedin_url,
        "recommendations_mentioned": recommendations,
        "recommendation_count": rec_count,
        "endorsements_mentioned": endorsements,
        "connections_mentioned": connections,
        "connection_count": conn_count,
        "publications_mentioned": publications,
        "volunteer_mentioned": volunteer,
    }


def score_linkedin(signals: dict[str, Any], role_type: str = "backend") -> float:
    """
    Score LinkedIn presence based on extracted signals.

    Weights:
        has_linkedin             — 30% (baseline presence)
        recommendations          — 25% (social proof)
        connections              — 15% (network breadth)
        publications             — 15% (thought leadership)
        volunteer/mentoring      — 15% (community engagement)

    Args:
        signals:   Dict from extract_linkedin_signals_from_resume().
        role_type: Role type for weight adjustments.

    Returns:
        Normalized score from 0.0 to 1.0.
    """
    if not signals or not signals.get("has_linkedin", False):
        return 0.0

    # Has LinkedIn profile
    presence_score = 1.0

    # Recommendations
    rec_count = signals.get("recommendation_count", 0)
    rec_score = min(rec_count / 5.0, 1.0) if rec_count > 0 else (
        0.5 if signals.get("recommendations_mentioned") else 0.0
    )

    # Connections
    conn_count = signals.get("connection_count", 0)
    if conn_count >= 500:
        conn_score = 1.0
    elif conn_count >= 200:
        conn_score = 0.7
    elif conn_count > 0:
        conn_score = 0.4
    elif signals.get("connections_mentioned"):
        conn_score = 0.3
    else:
        conn_score = 0.0

    # Publications
    pub_score = 1.0 if signals.get("publications_mentioned") else 0.0

    # Volunteer/mentoring
    vol_score = 1.0 if signals.get("volunteer_mentioned") else 0.0

    # For leadership roles, weight recommendations and network higher
    if role_type in ("tech_lead", "staff", "principal"):
        total = (
            presence_score * 0.20
            + rec_score * 0.30
            + conn_score * 0.20
            + pub_score * 0.15
            + vol_score * 0.15
        )
    else:
        total = (
            presence_score * 0.30
            + rec_score * 0.25
            + conn_score * 0.15
            + pub_score * 0.15
            + vol_score * 0.15
        )

    return round(min(max(total, 0.0), 1.0), 4)
