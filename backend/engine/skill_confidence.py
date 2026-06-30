"""
Skill Confidence Model — Determine confidence score and attributions for candidate skills.
"""

from typing import Any

def compute_skill_confidence(
    resume_features: dict[str, Any],
    linkedin_signals: dict[str, Any],
    github_signals: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Calculate confidence score and source attributions for each detected skill.
    
    Formula:
        - Presence on Resume: +30% base
        - Presence on LinkedIn: +20%
        - Presence on GitHub: +25%
        - Confirmed via Certifications: +10%
        - Mentioned in Projects: +10%
        - Supported by Experience Tenure (>2 years): +5%
        
    Args:
        resume_features: Dictionary containing 'skills', 'projects', 'certifications', 'experience'
        linkedin_signals: Dictionary containing LinkedIn details (skills, certifications, etc.)
        github_signals: Dictionary containing GitHub details (languages, repos)
        
    Returns:
        Dict mapping skill name (canonical) -> {
            "confidence": float (0-100),
            "evidence_count": int,
            "sources": list[str]
        }
    """
    skills_confidence = {}
    
    claimed_skills = resume_features.get("skills", [])
    projects = resume_features.get("projects", [])
    certs = resume_features.get("certifications", [])
    experience_years = resume_features.get("experience", 0.0)
    if isinstance(experience_years, list):
        # Fallback if list
        experience_years = len(experience_years)
    try:
        experience_years = float(experience_years)
    except (ValueError, TypeError):
        experience_years = 0.0
        
    # Gather other sources
    linkedin_skills = {s.lower() for s in linkedin_signals.get("skills", [])}
    if linkedin_signals.get("endorsements"):
        linkedin_skills.update({s.lower() for s in linkedin_signals["endorsements"].keys()})

    # Headline and experience descriptions matching
    linkedin_text = (
        linkedin_signals.get("headline", "") + " " +
        " ".join([exp.get("title", "") + " " + exp.get("description", "") for exp in linkedin_signals.get("experience", [])])
    ).lower()

    github_langs = {l.lower() for l in github_signals.get("languages", [])}
    github_repo_keywords = {k.lower() for k in github_signals.get("repo_keywords", [])}

    # Map frameworks/tools to base programming languages
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
    
    # Certifications text for matching
    certs_lower = " ".join([c.lower() for c in certs])
    
    # Projects text for matching
    projects_list = []
    for p in projects:
        if isinstance(p, dict):
            projects_list.append(p.get("title", "") + " " + p.get("description", ""))
        else:
            projects_list.append(str(p))
    projects_text = " ".join(projects_list).lower()
    
    for skill in claimed_skills:
        skill_lower = skill.lower()
        confidence = 0.0
        sources = []
        evidence_count = 0
        
        # 1. Resume Base (+30)
        confidence += 30.0
        sources.append("Resume")
        evidence_count += 1
        
        # 2. LinkedIn (+20)
        # Check if skill matches any LinkedIn skills, endorsements or experience/headline text
        skill_in_linkedin = (skill_lower in linkedin_skills) or any(s in linkedin_text for s in [skill_lower, skill_lower.replace(" ", "")])
        if linkedin_signals.get("has_linkedin") and skill_in_linkedin:
            confidence += 20.0
            sources.append("LinkedIn")
            evidence_count += 1
            
        # 3. GitHub (+25)
        # Check if language is on GitHub, or mapped base language is on GitHub, or matches repo name/topics/keywords
        has_github_evidence = False
        if skill_lower in github_langs:
            has_github_evidence = True
        elif skill_lower in tech_to_lang_map and tech_to_lang_map[skill_lower] in github_langs:
            has_github_evidence = True
        elif skill_lower in github_repo_keywords:
            has_github_evidence = True
        elif any(skill_lower in r for r in github_repo_keywords):
            has_github_evidence = True

        if has_github_evidence:
            confidence += 25.0
            sources.append("GitHub")
            evidence_count += 1
            
        # 4. Certifications (+10)
        # Check if certification mentions the skill (e.g. AWS SAA for AWS skill, CKA for Kubernetes skill)
        # Or if the skill matches any cert name
        skill_in_cert = False
        if skill_lower in certs_lower:
            skill_in_cert = True
        else:
            # Custom mappings
            mappings = {
                "aws": ["aws", "amazon web services", "saa", "sap"],
                "kubernetes": ["kubernetes", "cka", "ckad", "cks"],
                "docker": ["docker", "dca"],
                "java": ["ocpjp", "java"],
                "python": ["python", "pcap"],
                "security": ["security+", "cissp", "ceh"],
            }
            for k, synonyms in mappings.items():
                if skill_lower == k and any(syn in certs_lower for syn in synonyms):
                    skill_in_cert = True
                    break
                    
        if skill_in_cert:
            confidence += 10.0
            sources.append("Certifications")
            evidence_count += 1
            
        # 5. Projects (+10)
        if skill_lower in projects_text:
            confidence += 10.0
            sources.append("Projects")
            evidence_count += 1
            
        # 6. Experience Tenure (+5)
        if experience_years >= 2.0:
            confidence += 5.0
            sources.append("Tenure")
            evidence_count += 1
            
        skills_confidence[skill] = {
            "confidence": round(confidence, 1),
            "evidence_count": evidence_count,
            "sources": sources
        }
        
    return skills_confidence
