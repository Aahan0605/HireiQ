"""
Claim Verifier — Cross-reference resume claims against external signals.

Runs 5 verification checks to detect inconsistencies between what a
candidate claims on their resume and what external signals evidence.

Produces a trust_score (1.0 = fully trusted, deductions for each flag)
and a structured list of flags with severity levels.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Programming languages that SHOULD appear on GitHub if claimed
# ─────────────────────────────────────────────────────────────
PROGRAMMING_LANGUAGES: set[str] = {
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r",
    "matlab", "perl", "haskell", "elixir", "erlang", "clojure",
    "dart", "lua", "julia", "groovy", "objective-c", "f#",
    "visual basic", "assembly", "fortran", "cobol", "lisp",
    "scheme", "prolog", "ocaml", "zig", "nim", "crystal",
    "coffeescript", "actionscript", "vhdl", "verilog", "solidity",
    "move", "cairo", "vyper", "hack", "apex", "abap",
    "tcl", "ada", "d", "pascal", "delphi", "powershell",
    "bash", "shell", "sql",
}

# Skills that legitimately won't appear in GitHub repos
ALLOW_NO_GITHUB: set[str] = {
    "agile", "scrum", "kanban", "jira", "confluence", "trello",
    "project management", "team leadership", "mentoring",
    "communication", "problem solving", "critical thinking",
    "time management", "leadership", "stakeholder management",
    "product management", "business analysis", "requirements gathering",
    "system design", "architecture", "microservices",
    "ci/cd", "devops", "sre", "incident management",
    "technical writing", "documentation",
    "rest", "graphql", "grpc", "websocket",
    "oauth", "jwt", "ssl", "tls",
    "unit testing", "integration testing", "e2e testing",
    "tdd", "bdd", "pair programming", "code review",
    "a/b testing", "analytics", "seo",
    "figma", "sketch", "adobe xd", "photoshop",
    "linux", "windows", "macos",
    "networking", "security", "compliance",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data analysis", "data visualization", "statistics",
    "excel", "tableau", "power bi", "looker",
    "salesforce", "sap", "oracle",
}


def verify_claims(
    resume_features: dict[str, Any],
    external_signals: dict[str, Any],
) -> dict[str, Any]:
    """
    Cross-reference resume claims against external evidence.

    Runs 5 checks:
        1. Skill vs. GitHub languages
        2. Experience duration vs. LinkedIn
        3. Certification verification status
        4. Activity timeline consistency
        5. Portfolio vs. claimed tech stack

    Args:
        resume_features: Dict from feature_extractor.extract_features().
            Expected keys: skills, experience, education, certifications, raw_text
        external_signals: Dict with optional keys:
            - github: dict from fetch_github_signals()
            - linkedin: dict from extract_linkedin_signals_from_resume()
            - certifications: list of verified cert dicts
            - portfolio: dict from crawl_portfolio()

    Returns:
        Dict with:
            trust_score:     float (0.0–1.0, starts at 1.0)
            flags:           list of flag dicts
            verdict:         str summary
            verified_skills: skills that passed checks
            flagged_skills:  skills that failed checks
    """
    trust_score = 1.0
    flags: list[dict[str, Any]] = []
    verified_skills: list[str] = []
    flagged_skills: list[str] = []

    claimed_skills = [s.lower() for s in resume_features.get("skills", [])]
    claimed_experience = resume_features.get("experience", 0.0)

    github_data = external_signals.get("github", {})
    linkedin_data = external_signals.get("linkedin", {})
    cert_data = external_signals.get("certifications", [])
    portfolio_data = external_signals.get("portfolio", {})

    # ─── CHECK 1: Skill vs. GitHub Languages ───
    trust_score, flags, verified_skills, flagged_skills = _check_skill_vs_github(
        claimed_skills, github_data,
        trust_score, flags, verified_skills, flagged_skills,
    )

    # ─── CHECK 2: Experience Duration vs. LinkedIn ───
    trust_score, flags = _check_experience_vs_linkedin(
        claimed_experience, linkedin_data,
        trust_score, flags,
    )

    # ─── CHECK 3: Certification Verification ───
    trust_score, flags = _check_certifications(
        cert_data, trust_score, flags,
    )

    # ─── CHECK 4: Activity Timeline Consistency ───
    trust_score, flags = _check_timeline_consistency(
        claimed_experience, github_data,
        trust_score, flags,
    )

    # ─── CHECK 5: Portfolio vs. Claimed Stack ───
    trust_score, flags = _check_portfolio_vs_stack(
        claimed_skills, portfolio_data,
        trust_score, flags,
    )

    # Clamp trust score
    trust_score = round(max(0.0, min(1.0, trust_score)), 4)

    # Generate verdict
    verdict = _compute_verdict(trust_score, flags)

    return {
        "trust_score": trust_score,
        "flags": flags,
        "verdict": verdict,
        "verified_skills": sorted(set(verified_skills)),
        "flagged_skills": sorted(set(flagged_skills)),
        "total_checks_run": 5,
        "flags_count": len(flags),
    }


def _check_skill_vs_github(
    claimed_skills: list[str],
    github_data: dict,
    trust_score: float,
    flags: list[dict],
    verified_skills: list[str],
    flagged_skills: list[str],
) -> tuple[float, list[dict], list[str], list[str]]:
    """CHECK 1: Verify claimed programming skills against GitHub languages."""
    if not github_data or not github_data.get("languages"):
        # No GitHub data — can't verify, don't penalize
        return trust_score, flags, verified_skills, flagged_skills

    github_langs = {lang.lower() for lang in github_data.get("languages", [])}

    for skill in claimed_skills:
        skill_lower = skill.lower()

        # Only check programming languages
        if skill_lower not in PROGRAMMING_LANGUAGES:
            continue

        # Skip skills that legitimately don't appear on GitHub
        if skill_lower in ALLOW_NO_GITHUB:
            verified_skills.append(skill)
            continue

        if skill_lower in github_langs:
            verified_skills.append(skill)
        else:
            # Check common aliases
            aliases = _get_language_aliases(skill_lower)
            if aliases & github_langs:
                verified_skills.append(skill)
            else:
                flagged_skills.append(skill)
                deduction = 0.05
                trust_score -= deduction
                flags.append({
                    "type": "skill_not_evidenced",
                    "claim": f"Claims proficiency in '{skill}'",
                    "evidence": f"Not found in GitHub repos (found: {', '.join(sorted(github_langs)[:5])})",
                    "severity": "medium",
                    "deduction": deduction,
                })

    return trust_score, flags, verified_skills, flagged_skills


def _check_experience_vs_linkedin(
    claimed_experience: float,
    linkedin_data: dict,
    trust_score: float,
    flags: list[dict],
) -> tuple[float, list[dict]]:
    """CHECK 2: Compare experience years between resume and LinkedIn signals."""
    if not linkedin_data:
        return trust_score, flags

    # LinkedIn experience estimation from connection/recommendation signals
    # If we had actual LinkedIn data, we'd compare directly.
    # With resume-extracted signals, we check for consistency markers.
    linkedin_years = linkedin_data.get("experience_years", None)

    if linkedin_years is None:
        # Try to infer from account age or connection count
        conn_count = linkedin_data.get("connection_count", 0)
        rec_count = linkedin_data.get("recommendation_count", 0)

        # Heuristic: very high experience claim with zero LinkedIn presence
        if claimed_experience >= 8 and conn_count == 0 and rec_count == 0:
            if not linkedin_data.get("has_linkedin", False):
                deduction = 0.15
                trust_score -= deduction
                flags.append({
                    "type": "experience_mismatch",
                    "claim": f"Claims {claimed_experience:.0f} years experience",
                    "evidence": "No LinkedIn profile found for a senior candidate",
                    "severity": "high",
                    "deduction": deduction,
                })
        return trust_score, flags

    delta = abs(claimed_experience - linkedin_years)
    if delta > 1.5:
        deduction = 0.15
        trust_score -= deduction
        flags.append({
            "type": "experience_mismatch",
            "claim": f"Resume states {claimed_experience:.1f} years experience",
            "evidence": f"LinkedIn indicates {linkedin_years:.1f} years (delta: {delta:.1f})",
            "severity": "high",
            "deduction": deduction,
        })

    return trust_score, flags


def _check_certifications(
    cert_data: list[dict],
    trust_score: float,
    flags: list[dict],
) -> tuple[float, list[dict]]:
    """CHECK 3: Flag unverified certifications with low confidence."""
    if not cert_data:
        return trust_score, flags

    for cert in cert_data:
        verified = cert.get("verified", False)
        confidence = cert.get("confidence", 0.5)
        cert_name = cert.get("cert_name", cert.get("name", "Unknown"))

        if not verified and confidence < 0.5:
            deduction = 0.20
            trust_score -= deduction
            flags.append({
                "type": "cert_unverified",
                "claim": f"Claims certification: '{cert_name}'",
                "evidence": f"Verification failed (confidence: {confidence:.0%})",
                "severity": "high",
                "deduction": deduction,
            })

    return trust_score, flags


def _check_timeline_consistency(
    claimed_experience: float,
    github_data: dict,
    trust_score: float,
    flags: list[dict],
) -> tuple[float, list[dict]]:
    """CHECK 4: Compare claimed experience duration with GitHub account age."""
    if not github_data or not github_data.get("account_age_years"):
        return trust_score, flags

    account_age = github_data["account_age_years"]

    # If resume claims significantly more experience than GitHub account age
    if claimed_experience > account_age + 2:
        # This is a soft check — many devs join GitHub late
        # Only flag if the gap is substantial
        gap = claimed_experience - account_age
        if gap > 5:
            severity = "high"
            deduction = 0.10
        else:
            severity = "medium"
            deduction = 0.10

        trust_score -= deduction
        flags.append({
            "type": "timeline_inconsistency",
            "claim": f"Claims {claimed_experience:.0f} years experience",
            "evidence": (
                f"GitHub account is {account_age:.1f} years old "
                f"(gap: {gap:.1f} years). May have joined GitHub later."
            ),
            "severity": severity,
            "deduction": deduction,
        })

    return trust_score, flags


def _check_portfolio_vs_stack(
    claimed_skills: list[str],
    portfolio_data: dict,
    trust_score: float,
    flags: list[dict],
) -> tuple[float, list[dict]]:
    """CHECK 5: Compare claimed tech stack with portfolio evidence."""
    if not portfolio_data or not portfolio_data.get("tech_stack_mentioned"):
        return trust_score, flags

    # Count framework-level skills (not just languages)
    framework_skills = {
        "react", "angular", "vue", "svelte", "next.js", "nuxt",
        "node.js", "express", "fastapi", "django", "flask", "spring boot",
        "rails", "laravel", "asp.net", "nestjs", "gatsby", "remix",
    }

    claimed_frameworks = [s for s in claimed_skills if s.lower() in framework_skills]
    portfolio_tech = {t.lower() for t in portfolio_data.get("tech_stack_mentioned", [])}
    portfolio_frameworks = [f for f in claimed_frameworks if f.lower() in portfolio_tech]

    if len(claimed_frameworks) >= 5 and len(portfolio_frameworks) < 2:
        deduction = 0.05
        trust_score -= deduction
        flags.append({
            "type": "portfolio_mismatch",
            "claim": f"Claims {len(claimed_frameworks)} frameworks: {', '.join(claimed_frameworks[:5])}",
            "evidence": (
                f"Portfolio only evidences {len(portfolio_frameworks)} of them. "
                f"Portfolio tech: {', '.join(sorted(portfolio_tech)[:5])}"
            ),
            "severity": "low",
            "deduction": deduction,
        })

    return trust_score, flags


def _compute_verdict(trust_score: float, flags: list[dict]) -> str:
    """Generate a human-readable verdict based on trust_score and flags."""
    high_flags = sum(1 for f in flags if f.get("severity") == "high")
    total_flags = len(flags)

    if trust_score >= 0.90 and total_flags == 0:
        return "High confidence"
    elif trust_score >= 0.75 and high_flags == 0:
        return "Verify flagged items"
    elif trust_score >= 0.50 or high_flags <= 1:
        return "Significant discrepancies"
    else:
        return "Multiple red flags"


def _get_language_aliases(lang: str) -> set[str]:
    """Return common aliases for a programming language."""
    alias_map: dict[str, set[str]] = {
        "javascript": {"js", "ecmascript"},
        "typescript": {"ts"},
        "c++":        {"cpp", "cplusplus", "c plus plus"},
        "c#":         {"csharp", "c sharp"},
        "python":     {"py", "python3", "cpython"},
        "ruby":       {"rb"},
        "golang":     {"go"},
        "go":         {"golang"},
        "rust":       {"rs"},
        "kotlin":     {"kt"},
        "swift":      {"swift"},
        "scala":      {"sc"},
        "shell":      {"bash", "sh", "zsh", "fish"},
        "bash":       {"shell", "sh"},
        "sql":        {"plsql", "tsql", "mysql", "postgresql"},
        "objective-c":{"objc", "objectivec"},
        "f#":         {"fsharp"},
        "visual basic":{"vb", "vb.net", "vba"},
    }
    return alias_map.get(lang, set())
