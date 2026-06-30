"""
Candidate Matcher — Calculate detailed match breakdown against a job description.
"""

from typing import Any

def compute_match_breakdown(
    resume_features: dict[str, Any],
    jd_features: dict[str, Any],
    github_signals: dict[str, Any],
    linkedin_signals: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate breakdown match percentages for Skills, Experience, Education, Projects, and GitHub.
    """
    # 1. Skills Match %
    jd_required = {s.lower() for s in jd_features.get("required_skills", [])}
    jd_preferred = {s.lower() for s in jd_features.get("preferred_skills", [])}
    all_jd_skills = jd_required | jd_preferred
    
    claimed_skills = {s.lower() for s in resume_features.get("skills", [])}
    
    if all_jd_skills:
        # Check direct and semantic matching
        # Add basic synonym mappings for matcher
        synonyms = {
            "react.js": "react", "reactjs": "react",
            "js": "javascript", "ts": "typescript",
            "postgres": "postgresql", "k8s": "kubernetes"
        }
        matched_count = 0
        for s in all_jd_skills:
            if s in claimed_skills:
                matched_count += 1
            elif s in synonyms and synonyms[s] in claimed_skills:
                matched_count += 1
            elif any(synonyms.get(cs) == s for cs in claimed_skills):
                matched_count += 1
        skills_match = (matched_count / len(all_jd_skills)) * 100.0
    else:
        skills_match = 100.0 if claimed_skills else 50.0

    # 2. Experience Match %
    claimed_exp = 0.0
    try:
        claimed_exp = float(resume_features.get("experience", 0.0))
    except (ValueError, TypeError):
        pass
        
    required_exp = 0.0
    try:
        required_exp = float(jd_features.get("min_experience", 0.0))
    except (ValueError, TypeError):
        pass
        
    if required_exp > 0:
        exp_match = min((claimed_exp / required_exp) * 100.0, 100.0)
    else:
        exp_match = 100.0

    # 3. Education Match %
    claimed_edu = resume_features.get("education", "unknown")
    required_edu = jd_features.get("education_required", "unknown")
    
    degree_hierarchy = ["unknown", "high_school", "diploma", "associate", "bca", "bsc", "be", "btech", "bs", "bachelors", "mba", "msc", "mtech", "ms", "masters", "phd"]
    
    try:
        claimed_idx = degree_hierarchy.index(claimed_edu) if claimed_edu in degree_hierarchy else 0
        required_idx = degree_hierarchy.index(required_edu) if required_edu in degree_hierarchy else 0
        
        if claimed_idx >= required_idx:
            edu_match = 100.0
        else:
            edu_match = max(0.0, (claimed_idx / max(required_idx, 1)) * 100.0)
    except Exception:
        edu_match = 50.0

    # 4. Projects Match %
    projects = resume_features.get("projects", [])
    project_match = 0.0
    if projects and all_jd_skills:
        # Check how many projects mention at least one JD skill
        matching_projects = 0
        project_text_combined = ""
        for p in projects:
            if isinstance(p, dict):
                p_text = (p.get("title", "") + " " + p.get("description", "")).lower()
            else:
                p_text = str(p).lower()
            project_text_combined += " " + p_text
            
        matched_project_skills = sum(1 for s in all_jd_skills if s in project_text_combined)
        project_match = min((matched_project_skills / max(len(all_jd_skills), 1)) * 100.0, 100.0)
        # Give a boost for having projects
        project_match = min(30.0 + (project_match * 0.7), 100.0)
    elif projects:
        project_match = 70.0
    else:
        project_match = 0.0

    # 5. GitHub Match %
    has_github = github_signals.get("total_repos", 0) > 0 or github_signals.get("account_age_years", 0) > 0
    if has_github:
        # Scale based on stars and commit frequency
        stars = github_signals.get("total_stars", 0)
        freq = github_signals.get("commit_frequency_per_week", 0.0)
        github_match = min(40.0 + (stars * 2.0) + (freq * 5.0), 100.0)
    else:
        github_match = 0.0

    # Overall Match %
    overall = (skills_match * 0.40) + (exp_match * 0.25) + (project_match * 0.15) + (github_match * 0.10) + (edu_match * 0.10)

    return {
        "skills_match": round(skills_match, 1),
        "experience_match": round(exp_match, 1),
        "education_match": round(edu_match, 1),
        "projects_match": round(project_match, 1),
        "github_match": round(github_match, 1),
        "overall_match_percentage": round(overall, 1)
    }
