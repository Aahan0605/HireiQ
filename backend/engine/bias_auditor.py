"""
Bias Auditor — Detect and measure scoring bias in candidate evaluation.

Provides:
    1. create_blind_features() — Anonymize candidate data
    2. audit_bias()            — Compare full vs. blind scores
    3. run_batch_bias_audit()  — Aggregate bias metrics across candidates

Goal: Ensure scoring is based on skills and evidence, not identity.
"""

from __future__ import annotations

import copy
import logging
import math
import re
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Gender indicators (pronouns, honorifics, gendered terms)
# ─────────────────────────────────────────────────────────────
GENDER_INDICATORS: list[str] = [
    # Pronouns
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "they", "them", "their", "themself", "themselves",
    # Honorifics
    "mr.", "mr", "mrs.", "mrs", "ms.", "ms", "miss",
    "dr.", "dr", "prof.", "prof",
    "sir", "madam", "ma'am",
    # Gendered nouns
    "father", "mother", "husband", "wife",
    "son", "daughter", "brother", "sister",
    "boyfriend", "girlfriend",
    "paternity", "maternity",
    "chairman", "chairwoman", "chairperson",
    "spokesman", "spokeswoman",
    "businessman", "businesswoman",
    "fireman", "firewoman",
    "policeman", "policewoman",
    "salesman", "saleswoman",
]

# ─────────────────────────────────────────────────────────────
# Name patterns by region (for detection, NOT scoring)
# These are used ONLY to identify what to REDACT.
# ─────────────────────────────────────────────────────────────
NAME_PATTERNS: dict[str, list[str]] = {
    "south_asian": [
        r"\b\w+(?:kumar|singh|sharma|patel|gupta|joshi|reddy|rao|nair|iyer|"
        r"verma|mishra|pandey|agarwal|srivastava|chopra|mehta|kapoor|bhatt)\b"
    ],
    "east_asian": [
        r"\b(?:zhang|wang|li|liu|chen|yang|huang|zhao|wu|zhou|xu|sun|"
        r"ma|zhu|hu|guo|lin|luo|tang|kim|park|lee|choi|jung|"
        r"kang|yoon|jang|tanaka|suzuki|takahashi|sato|watanabe)\b"
    ],
    "european": [
        r"\b\w+(?:ov|ova|ski|ska|enko|enko|sson|dottir|mann|stein|berg|"
        r"ström|lund|gren|qvist|feld|burg|bauer|müller|schmidt)\b"
    ],
    "middle_eastern": [
        r"\b(?:al-|el-|bin\s|ibn\s|abu\s)\w+\b",
        r"\b\w+(?:zadeh|pour|nejad|khani|far|yar|yari)\b",
    ],
    "african": [
        r"\b\w+(?:dze|oku|afor|ofor|ango|ongo|kwe|nke|mba|ndi|chi)\b"
    ],
    "hispanic": [
        r"\b\w+(?:ez|az|oz|iz|ñ)\b",
    ],
}

# Fields to redact for blind evaluation
_IDENTITY_FIELDS: set[str] = {
    "candidate_name", "name", "full_name", "first_name", "last_name",
    "photo_url", "avatar_url", "profile_photo", "image_url",
    "email", "phone", "address", "location", "city", "state",
    "gender", "age", "date_of_birth", "dob", "nationality",
    "ethnicity", "race", "religion", "marital_status",
    "linkedin_url", "linkedin_profile",
    "photo", "avatar", "headshot",
}


def redact_resume_text(resume_text: str) -> str:
    """
    Fully redact raw resume text for blind evaluation mode.
    Redacts names, gender indicators, emails, phone numbers, and URLs.
    """
    if not resume_text:
        return resume_text
    
    text = _redact_gender_indicators(resume_text)
    text = _redact_names(text)
    
    # Redact email addresses
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', text)
    # Redact phone numbers
    text = re.sub(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', '[PHONE REDACTED]', text)
    # Redact common URLs (LinkedIn, GitHub, etc)
    text = re.sub(r'https?://[^\s]+', '[URL REDACTED]', text)
    text = re.sub(r'(?:www\.)?[a-zA-Z0-9-]+\.(?:com|org|net|io|me)[/\w-]*', '[URL REDACTED]', text)
    
    return text


async def compute_blind_score(
    candidate_name: str,
    resume_text: str,
    jd_features: dict[str, Any],
    role_type: str = "backend_engineer",
) -> dict[str, Any]:
    """
    Computes a fully blind score by redacting the raw text up front,
    parsing the redacted text into features, and preventing any signaling
    from external integrations like GitHub.
    """
    from engine.score_fusion import compute_full_candidate_score
    
    blind_text = redact_resume_text(resume_text)
    
    # Run the standard scoring engine with the redacted text
    # Exclude all external handles so they don't leak identity or bias
    result = await compute_full_candidate_score(
        candidate_name="[REDACTED]",
        resume_text=blind_text,
        jd_features=jd_features,
        github_username="",
        cf_handle="",
        cc_username="",
        lc_username="",
        portfolio_url="",
        role_type=role_type,
    )
    return result


def create_blind_features(
    resume_features: dict[str, Any],
) -> dict[str, Any]:
    """
    Create an anonymized copy of resume features for blind evaluation.

    Removes:
        - Candidate name, photo, contact info
        - Gender indicators from text fields
        - Any field that could reveal identity

    Args:
        resume_features: Original feature dict from extract_features().

    Returns:
        Deep-copied dict with identity fields removed/redacted.
    """
    blind = copy.deepcopy(resume_features)

    # ─── Remove identity fields ───
    for field in _IDENTITY_FIELDS:
        blind.pop(field, None)

    # ─── Redact gender indicators from text fields ───
    text_fields = ["raw_text", "summary", "objective", "bio", "about"]
    for field in text_fields:
        if field in blind and isinstance(blind[field], str):
            blind[field] = _redact_gender_indicators(blind[field])
            blind[field] = _redact_names(blind[field])

    # ─── Anonymize education institution names ───
    # Keep degree/field but redact specific institution identifiers
    # that might reveal demographic info
    if "education" in blind and isinstance(blind["education"], list):
        blind["education"] = [
            _anonymize_education_entry(e)
            if isinstance(e, str) else e
            for e in blind["education"]
        ]

    # ─── Remove location from work experience ───
    if "work_experience" in blind and isinstance(blind["work_experience"], list):
        for exp in blind["work_experience"]:
            if isinstance(exp, dict):
                exp.pop("location", None)
                exp.pop("city", None)
                exp.pop("company_location", None)

    return blind


def audit_bias(
    full_score: float,
    blind_score: float,
    candidate_name: str = "Anonymous",
) -> dict[str, Any]:
    """
    Compare a candidate's full score vs. their blind (anonymized) score.

    A significant delta suggests scoring may be influenced by identity
    factors rather than purely by skills and evidence.

    Args:
        full_score:     Score computed with full candidate data (0–100).
        blind_score:    Score computed with anonymized data (0–100).
        candidate_name: Candidate name (included in report, not in scoring).

    Returns:
        Dict with bias analysis:
            full_score, blind_score, bias_delta,
            bias_detected (bool), bias_direction, recommendation.
    """
    bias_delta = round(full_score - blind_score, 4)
    abs_delta = abs(bias_delta)

    bias_detected = abs_delta > 5.0

    if bias_delta > 5.0:
        bias_direction = "positive"
        recommendation = (
            f"Candidate '{candidate_name}' received {abs_delta:.1f} points "
            f"MORE with identity-visible scoring. Review for potential "
            f"positive bias (affinity, halo effect, or prestige bias)."
        )
    elif bias_delta < -5.0:
        bias_direction = "negative"
        recommendation = (
            f"Candidate '{candidate_name}' received {abs_delta:.1f} points "
            f"LESS with identity-visible scoring. Review for potential "
            f"negative bias (name bias, demographic bias, or affinity gap)."
        )
    else:
        bias_direction = "none"
        recommendation = (
            f"Scoring for '{candidate_name}' shows no significant identity-based "
            f"bias (delta: {abs_delta:.1f}, threshold: 5.0)."
        )

    return {
        "candidate_name": candidate_name,
        "full_score": round(full_score, 2),
        "blind_score": round(blind_score, 2),
        "bias_delta": round(bias_delta, 2),
        "abs_delta": round(abs_delta, 2),
        "bias_detected": bias_detected,
        "bias_direction": bias_direction,
        "recommendation": recommendation,
    }


def run_batch_bias_audit(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate bias audit across all candidates in a batch.

    Args:
        results: List of dicts from audit_bias().

    Returns:
        Dict with aggregate metrics:
            mean_delta, std_delta, max_delta,
            flagged_count, flagged_candidates,
            total_candidates, overall_fair (bool).
    """
    if not results:
        return {
            "mean_delta": 0.0,
            "std_delta": 0.0,
            "max_delta": 0.0,
            "flagged_count": 0,
            "flagged_candidates": [],
            "total_candidates": 0,
            "overall_fair": True,
            "fairness_grade": "A",
        }

    deltas = [r.get("bias_delta", 0.0) for r in results]
    abs_deltas = [abs(d) for d in deltas]
    n = len(deltas)

    mean_delta = sum(deltas) / n
    variance = sum((d - mean_delta) ** 2 for d in deltas) / max(n - 1, 1)
    std_delta = math.sqrt(variance)
    max_delta = max(abs_deltas)

    flagged = [r for r in results if r.get("bias_detected", False)]
    flagged_candidates = [
        {
            "name": r.get("candidate_name", "Unknown"),
            "delta": r.get("bias_delta", 0.0),
            "direction": r.get("bias_direction", "none"),
        }
        for r in flagged
    ]

    flagged_ratio = len(flagged) / n if n > 0 else 0.0

    # Overall fairness: fair if <15% are flagged AND std_delta < 5
    overall_fair = flagged_ratio < 0.15 and std_delta < 5.0

    # Fairness grade
    if flagged_ratio == 0 and std_delta < 2.0:
        grade = "A"
    elif flagged_ratio < 0.05 and std_delta < 3.0:
        grade = "A-"
    elif flagged_ratio < 0.10 and std_delta < 4.0:
        grade = "B+"
    elif flagged_ratio < 0.15 and std_delta < 5.0:
        grade = "B"
    elif flagged_ratio < 0.25:
        grade = "C"
    else:
        grade = "D"

    return {
        "mean_delta": round(mean_delta, 4),
        "std_delta": round(std_delta, 4),
        "max_delta": round(max_delta, 4),
        "flagged_count": len(flagged),
        "flagged_candidates": flagged_candidates,
        "total_candidates": n,
        "flagged_ratio": round(flagged_ratio, 4),
        "overall_fair": overall_fair,
        "fairness_grade": grade,
    }


# ─────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────

def _redact_gender_indicators(text: str) -> str:
    """Remove gender-coded terms from text."""
    if not text:
        return text

    for indicator in GENDER_INDICATORS:
        # Replace whole words only, case-insensitive
        pattern = re.compile(
            r'\b' + re.escape(indicator) + r'\b',
            re.IGNORECASE,
        )
        text = pattern.sub("[REDACTED]", text)

    return text


def _redact_names(text: str) -> str:
    """
    Redact names matching regional surname patterns.

    Note: This is a best-effort redaction. It may miss some names
    or redact non-name words. For production, use a dedicated NER model.
    """
    if not text:
        return text

    for _region, patterns in NAME_PATTERNS.items():
        for pattern_str in patterns:
            try:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                text = pattern.sub("[REDACTED]", text)
            except re.error:
                # Skip invalid patterns
                continue

    return text


def _anonymize_education_entry(entry: str) -> str:
    """
    Anonymize an education entry by keeping degree type but
    redacting institution name hints that might reveal demographics.

    Keeps: "Bachelor's in Computer Science"
    Redacts: institution-specific identifiers
    """
    if not entry:
        return entry

    # Preserve degree type and field
    degree_patterns = [
        r"((?:ph\.?d|doctorate|master'?s?|bachelor'?s?|associate'?s?|"
        r"b\.?s\.?|m\.?s\.?|b\.?tech|m\.?tech|b\.?e\.?|m\.?e\.?|"
        r"b\.?c\.?a\.?|m\.?c\.?a\.?|m\.?b\.?a\.?)\s*"
        r"(?:in|of)?\s*[\w\s]+)",
    ]

    for pat in degree_patterns:
        match = re.search(pat, entry, re.IGNORECASE)
        if match:
            return match.group(0).strip()

    # If no degree pattern found, return as-is (likely just the degree)
    return entry
