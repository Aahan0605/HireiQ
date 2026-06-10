"""
Candidate Ranker — Compute composite ranking scores and generate recruiter justifications.
"""

from typing import Any

def compute_composite_rank_score(
    all_scores: dict[str, float],
    candidate_name: str,
    role_type: str = "backend_engineer"
) -> dict[str, Any]:
    """
    Compute a composite ranking score for a candidate.
    
    Formula:
        Final score = 0.35 * ATS_Score 
                    + 0.20 * Experience_Score 
                    + 0.15 * Project_Match 
                    + 0.15 * GitHub_Evidence 
                    + 0.15 * LinkedIn_Evidence 
                    + Cert_Bonus
                    
    Args:
        all_scores: Dictionary of raw scores from 0.0 to 1.0 or 0.0 to 100.0:
            - resume_skill_match / ats_score
            - resume_experience
            - project_score / portfolio_score
            - github_score / engineering_score
            - linkedin_score
            - certification_score
        candidate_name: Candidate name
        role_type: Targeted job role
        
    Returns:
        Dict containing:
            - final_score: float (0.0 to 100.0)
            - breakdown: dict
            - justification: str
    """
    # Normalize inputs (assumes values are either 0-1 or 0-100)
    def normalize(val):
        if val is None:
            return 0.0
        return val * 100.0 if val <= 1.0 else val

    ats_score = normalize(all_scores.get("resume_skill_match", 0.0))
    exp_score = normalize(all_scores.get("resume_experience", 0.0))
    project_score = normalize(all_scores.get("portfolio_score", all_scores.get("project_score", 0.0)))
    github_score = normalize(all_scores.get("github_score", all_scores.get("engineering_score", 0.0)))
    linkedin_score = normalize(all_scores.get("linkedin_score", 0.0))
    cert_score = normalize(all_scores.get("certification_score", 0.0))

    # Calculate base composite
    weighted_score = (
        0.35 * ats_score +
        0.20 * exp_score +
        0.15 * project_score +
        0.15 * github_score +
        0.15 * linkedin_score
    )

    # Cert Bonus: up to 5 points
    cert_bonus = min(cert_score * 0.05, 5.0)
    final_score = round(min(weighted_score + cert_bonus, 100.0), 2)

    # Build recruiter-grade justification
    strengths = []
    gaps = []

    if ats_score >= 80:
        strengths.append(f"strong skill alignment ({ats_score:.0f}% ATS match)")
    elif ats_score < 50:
        gaps.append(f"gaps in core required tech stack")

    if exp_score >= 80:
        strengths.append("excellent experience tenure")
    elif exp_score < 50:
        gaps.append("years of experience falls short of target requirements")

    if github_score >= 75:
        strengths.append("high-quality open-source and active engineering presence on GitHub")
    elif github_score < 40 and github_score > 0:
        gaps.append("limited coding activity or repository maintenance on GitHub")

    if linkedin_score >= 75:
        strengths.append("strong professional presence with verified social signals")

    justification_parts = []
    if strengths:
        justification_parts.append(f"{candidate_name} demonstrates " + ", ".join(strengths) + ".")
    else:
        justification_parts.append(f"{candidate_name} meets the baseline criteria for the role.")

    if gaps:
        justification_parts.append("Area of focus / verification recommended: " + ", ".join(gaps) + ".")
    else:
        justification_parts.append("Profile presents low technical risk with solid evidence across all indicators.")

    justification = " ".join(justification_parts)

    return {
        "final_score": final_score,
        "breakdown": {
            "ats_match": round(ats_score, 1),
            "experience_match": round(exp_score, 1),
            "projects_match": round(project_score, 1),
            "github_match": round(github_score, 1),
            "linkedin_match": round(linkedin_score, 1),
            "cert_bonus": round(cert_bonus, 1)
        },
        "justification": justification
    }
