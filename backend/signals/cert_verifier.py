"""
Certification Verifier — Detection and verification of professional certs.

Detects certification mentions in resume text via regex, then attempts
automated verification where possible (Coursera, Credly).

Unverifiable certs are flagged for manual review with a lower confidence
score. All network operations are async with 10-second timeout.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TIMEOUT = 10.0

# ─────────────────────────────────────────────────────────────
# Certification Detection Patterns
# Each key = issuer, value = list of (display_name, regex_pattern)
# ─────────────────────────────────────────────────────────────
CERT_PATTERNS: dict[str, list[tuple[str, re.Pattern]]] = {
    "AWS": [
        ("AWS Certified Cloud Practitioner (CCP)",
         re.compile(r"aws\s+(?:certified\s+)?cloud\s+practitioner|clf[\s-]?c0[12]|ccp", re.I)),
        ("AWS Certified Solutions Architect Associate (SAA)",
         re.compile(r"solutions?\s+architect\s+(?:associate|assoc)|saa[\s-]?c0[23]|aws\s+saa", re.I)),
        ("AWS Certified Solutions Architect Professional (SAP)",
         re.compile(r"solutions?\s+architect\s+(?:professional|prof)|sap[\s-]?c0[12]|aws\s+sap", re.I)),
        ("AWS Certified Developer Associate (DVA)",
         re.compile(r"aws\s+(?:certified\s+)?developer\s+associate|dva[\s-]?c0[12]|aws\s+dva", re.I)),
        ("AWS Certified SysOps Administrator",
         re.compile(r"sysops\s+admin|soa[\s-]?c0[12]", re.I)),
        ("AWS Certified DevOps Engineer Professional",
         re.compile(r"devops\s+engineer\s+professional|dop[\s-]?c0[12]", re.I)),
        ("AWS Certified Machine Learning Specialty",
         re.compile(r"aws\s+(?:certified\s+)?machine\s+learning|mls[\s-]?c01", re.I)),
        ("AWS Certified Security Specialty",
         re.compile(r"aws\s+(?:certified\s+)?security\s+specialty|scs[\s-]?c0[12]", re.I)),
        ("AWS Certified Data Analytics Specialty",
         re.compile(r"aws\s+(?:certified\s+)?data\s+analytics|das[\s-]?c01", re.I)),
    ],
    "GCP": [
        ("Google Cloud Associate Cloud Engineer (ACE)",
         re.compile(r"associate\s+cloud\s+engineer|gcp\s+ace|google\s+cloud\s+ace", re.I)),
        ("Google Cloud Professional Cloud Architect (PCE)",
         re.compile(r"professional\s+cloud\s+architect|gcp\s+pca|google\s+cloud\s+architect", re.I)),
        ("Google Cloud Professional Data Engineer",
         re.compile(r"professional\s+data\s+engineer|gcp\s+(?:professional\s+)?data\s+engineer", re.I)),
        ("Google Cloud Professional ML Engineer",
         re.compile(r"professional\s+(?:ml|machine\s+learning)\s+engineer|gcp\s+ml", re.I)),
        ("Google Cloud Digital Leader",
         re.compile(r"(?:google\s+)?cloud\s+digital\s+leader|cdl", re.I)),
    ],
    "Azure": [
        ("Azure Fundamentals (AZ-900)",
         re.compile(r"az[\s-]?900|azure\s+fundamentals", re.I)),
        ("Azure Administrator (AZ-104)",
         re.compile(r"az[\s-]?104|azure\s+administrator", re.I)),
        ("Azure Developer Associate (AZ-204)",
         re.compile(r"az[\s-]?204|azure\s+developer\s+associate", re.I)),
        ("Azure Solutions Architect (AZ-305)",
         re.compile(r"az[\s-]?305|azure\s+solutions?\s+architect", re.I)),
        ("Azure DevOps Engineer (AZ-400)",
         re.compile(r"az[\s-]?400|azure\s+devops\s+engineer", re.I)),
        ("Azure Data Fundamentals (DP-900)",
         re.compile(r"dp[\s-]?900|azure\s+data\s+fundamentals", re.I)),
        ("Azure Data Engineer (DP-203)",
         re.compile(r"dp[\s-]?203|azure\s+data\s+engineer", re.I)),
        ("Azure AI Fundamentals (AI-900)",
         re.compile(r"ai[\s-]?900|azure\s+ai\s+fundamentals", re.I)),
        ("Azure AI Engineer (AI-102)",
         re.compile(r"ai[\s-]?102|azure\s+ai\s+engineer", re.I)),
    ],
    "Kubernetes": [
        ("Certified Kubernetes Administrator (CKA)",
         re.compile(r"\bcka\b|certified\s+kubernetes\s+admin", re.I)),
        ("Certified Kubernetes Application Developer (CKAD)",
         re.compile(r"\bckad\b|kubernetes\s+application\s+developer", re.I)),
        ("Certified Kubernetes Security Specialist (CKS)",
         re.compile(r"\bcks\b|kubernetes\s+security\s+specialist", re.I)),
    ],
    "Terraform": [
        ("HashiCorp Certified Terraform Associate",
         re.compile(r"terraform\s+associate|hashicorp\s+(?:certified\s+)?terraform", re.I)),
    ],
    "Coursera": [
        ("Coursera Professional Certificate",
         re.compile(r"coursera\s+(?:professional\s+)?certificate", re.I)),
        ("Google Data Analytics Certificate",
         re.compile(r"google\s+data\s+analytics\s+(?:professional\s+)?certificate", re.I)),
        ("Google IT Support Certificate",
         re.compile(r"google\s+it\s+support\s+(?:professional\s+)?certificate", re.I)),
        ("IBM Data Science Certificate",
         re.compile(r"ibm\s+data\s+science\s+(?:professional\s+)?certificate", re.I)),
        ("Meta Frontend Developer Certificate",
         re.compile(r"meta\s+(?:front[\s-]?end|frontend)\s+developer\s+certificate", re.I)),
        ("Meta Backend Developer Certificate",
         re.compile(r"meta\s+(?:back[\s-]?end|backend)\s+developer\s+certificate", re.I)),
    ],
    "edX": [
        ("edX Professional Certificate",
         re.compile(r"edx\s+(?:professional\s+)?certificate", re.I)),
        ("edX MicroMasters",
         re.compile(r"edx\s+micromasters?", re.I)),
    ],
    "HackerRank": [
        ("HackerRank Certification",
         re.compile(r"hackerrank\s+(?:certified|certification|skill\s+cert)", re.I)),
    ],
    "Other": [
        ("Certified Scrum Master (CSM)",
         re.compile(r"\bcsm\b|certified\s+scrum\s+master", re.I)),
        ("Project Management Professional (PMP)",
         re.compile(r"\bpmp\b|project\s+management\s+professional", re.I)),
        ("CISSP",
         re.compile(r"\bcissp\b|certified\s+information\s+systems?\s+security", re.I)),
        ("Certified Ethical Hacker (CEH)",
         re.compile(r"\bceh\b|certified\s+ethical\s+hacker", re.I)),
        ("CompTIA Security+",
         re.compile(r"comptia\s+security\s*\+|security\s*\+", re.I)),
        ("CompTIA Network+",
         re.compile(r"comptia\s+network\s*\+|network\s*\+", re.I)),
        ("Oracle Certified Professional (OCP)",
         re.compile(r"\bocp\b|oracle\s+certified\s+professional", re.I)),
        ("Databricks Certified",
         re.compile(r"databricks\s+certified", re.I)),
        ("MongoDB Certified Developer",
         re.compile(r"mongodb\s+certified", re.I)),
    ],
}

# Regex for cert IDs (Coursera, Credly, etc.)
CERT_ID_PATTERNS = [
    re.compile(r"(?:cert(?:ificate)?[\s#:]*(?:id)?[\s#:]*|credential[\s#:]*(?:id)?[\s#:]*)([A-Z0-9]{6,20})", re.I),
    re.compile(r"(?:verify|validation)[\s:]+(?:at\s+)?(?:https?://\S+/)?([A-Z0-9]{6,20})", re.I),
    re.compile(r"coursera\.org/(?:verify|account/accomplishments/certificate)/([A-Z0-9]+)", re.I),
    re.compile(r"credly\.com/badges/([a-f0-9\-]{36})", re.I),
]

# Date patterns for cert mention dates
DATE_PATTERN = re.compile(
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}|\d{1,2}/\d{4}|\d{4})",
    re.I,
)


def detect_certifications(text: str) -> list[dict[str, Any]]:
    """
    Detect professional certifications mentioned in resume text.

    Scans text against all known certification regex patterns and
    extracts cert names, issuers, IDs (if present), and dates.

    Args:
        text: Cleaned resume text.

    Returns:
        List of dicts, each with:
            - name: str (certification display name)
            - issuer: str (issuing organization)
            - cert_id: str | None (detected certificate ID)
            - mentioned_date: str | None (date string found near cert mention)

    Examples:
        >>> certs = detect_certifications("I hold AWS SAA-C03 and CKA certifications (Jan 2024)")
        >>> len(certs) >= 2
        True
    """
    if not text:
        return []

    detected: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for issuer, patterns in CERT_PATTERNS.items():
        for cert_name, pattern in patterns:
            match = pattern.search(text)
            if match and cert_name not in seen_names:
                seen_names.add(cert_name)

                # Try to find a cert ID near the match
                cert_id = _find_cert_id(text, match.start(), match.end())

                # Try to find a date near the match
                mentioned_date = _find_nearby_date(text, match.start(), match.end())

                detected.append({
                    "name": cert_name,
                    "issuer": issuer,
                    "cert_id": cert_id,
                    "mentioned_date": mentioned_date,
                })

    return detected


def _find_cert_id(text: str, match_start: int, match_end: int) -> str | None:
    """Search for a certificate ID within 200 chars of the cert mention."""
    window_start = max(0, match_start - 50)
    window_end = min(len(text), match_end + 200)
    window = text[window_start:window_end]

    for pattern in CERT_ID_PATTERNS:
        id_match = pattern.search(window)
        if id_match:
            return id_match.group(1)
    return None


def _find_nearby_date(text: str, match_start: int, match_end: int) -> str | None:
    """Search for a date within 100 chars of the cert mention."""
    window_start = max(0, match_start - 20)
    window_end = min(len(text), match_end + 100)
    window = text[window_start:window_end]

    date_match = DATE_PATTERN.search(window)
    if date_match:
        return date_match.group(0).strip()
    return None


async def verify_cert(cert: dict[str, Any]) -> dict[str, Any]:
    """
    Attempt automated verification of a certification.

    Currently supports:
        - Coursera: GET https://www.coursera.org/api/certificate.v1/{id}
        - Credly:   GET https://www.credly.com/badges/{id} (existence check)

    All other issuers return manual-verification-required status.

    Args:
        cert: Dict from detect_certifications() with name, issuer, cert_id.

    Returns:
        Dict with:
            - cert_name: str
            - issuer: str
            - verified: bool
            - confidence: float (0.0-1.0)
            - message: str
    """
    cert_name = cert.get("name", "Unknown")
    issuer = cert.get("issuer", "Unknown")
    cert_id = cert.get("cert_id")

    base_result = {
        "cert_name": cert_name,
        "issuer": issuer,
        "verified": False,
        "confidence": 0.0,
        "message": "",
    }

    if not cert_id:
        base_result["confidence"] = 0.4
        base_result["message"] = "No certificate ID found. Manual verification required."
        return base_result

    # Try Coursera verification
    if issuer == "Coursera":
        return await _verify_coursera(cert_id, base_result)

    # Try Credly verification (many vendors use Credly)
    if len(cert_id) == 36 and "-" in cert_id:  # UUID format = likely Credly badge
        return await _verify_credly(cert_id, base_result)

    # Cert ID found but no automated verification available
    base_result["confidence"] = 0.6
    base_result["message"] = (
        f"Certificate ID '{cert_id}' detected. "
        f"Manual verification required for {issuer}."
    )
    return base_result


async def _verify_coursera(cert_id: str, result: dict) -> dict:
    """Verify a Coursera certificate by ID."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://www.coursera.org/api/certificate.v1/{cert_id}",
                timeout=TIMEOUT,
                headers={"User-Agent": "HireIQ-Cert-Verifier/1.0"},
            )
            if resp.status_code == 200:
                result["verified"] = True
                result["confidence"] = 0.95
                result["message"] = f"Coursera certificate '{cert_id}' verified."
            elif resp.status_code == 404:
                result["verified"] = False
                result["confidence"] = 0.3
                result["message"] = f"Coursera certificate '{cert_id}' not found."
            else:
                result["confidence"] = 0.5
                result["message"] = f"Coursera API returned status {resp.status_code}."
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"Coursera verification failed: {e}")
        result["confidence"] = 0.4
        result["message"] = "Coursera verification service unavailable."

    return result


async def _verify_credly(badge_id: str, result: dict) -> dict:
    """Verify a Credly badge by checking if the page exists."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.head(
                f"https://www.credly.com/badges/{badge_id}",
                timeout=TIMEOUT,
                headers={"User-Agent": "HireIQ-Cert-Verifier/1.0"},
                follow_redirects=True,
            )
            if resp.status_code == 200:
                result["verified"] = True
                result["confidence"] = 0.90
                result["message"] = f"Credly badge '{badge_id}' verified."
            else:
                result["confidence"] = 0.4
                result["message"] = f"Credly badge not found (HTTP {resp.status_code})."
    except (httpx.TimeoutException, httpx.RequestError, Exception) as e:
        logger.warning(f"Credly verification failed: {e}")
        result["confidence"] = 0.4
        result["message"] = "Credly verification service unavailable."

    return result


def score_certifications(
    certs: list[dict[str, Any]],
    required_certs: list[str],
) -> float:
    """
    Score detected certifications against JD requirements.

    Scoring logic:
        1. Match detected certs against required certs (case-insensitive substring)
        2. Verified cert = 1.0 weight, unverified = 0.6 weight
        3. Score = weighted matches / total required
        4. Bonus for extra relevant certs beyond requirements

    Args:
        certs:          List of dicts with cert_name, verified, confidence.
        required_certs: List of cert name strings from JD.

    Returns:
        Normalized score from 0.0 to 1.0.
    """
    if not required_certs:
        # No specific certs required — give partial credit for having any
        if not certs:
            return 0.0
        base = min(len(certs) / 3.0, 0.6)  # up to 0.6 for having certs
        verified_count = sum(1 for c in certs if c.get("verified", False))
        bonus = verified_count * 0.1
        return round(min(base + bonus, 1.0), 4)

    if not certs:
        return 0.0

    # Match certs against requirements
    matched_weight = 0.0
    matched_count = 0

    for required in required_certs:
        req_lower = required.lower()
        best_match_weight = 0.0

        for cert in certs:
            cert_name = cert.get("cert_name", cert.get("name", "")).lower()
            if req_lower in cert_name or cert_name in req_lower:
                # Found a match
                if cert.get("verified", False):
                    weight = 1.0
                else:
                    confidence = cert.get("confidence", 0.5)
                    weight = max(0.6, confidence)
                best_match_weight = max(best_match_weight, weight)

        if best_match_weight > 0:
            matched_weight += best_match_weight
            matched_count += 1

    # Base score = weighted matches / total required
    score = matched_weight / len(required_certs)

    # Bonus for extra certs (up to 0.1)
    extra_certs = len(certs) - matched_count
    if extra_certs > 0:
        score += min(extra_certs * 0.03, 0.10)

    return round(min(max(score, 0.0), 1.0), 4)
