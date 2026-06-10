import os
import sys
from pathlib import Path
import json

# Add parent dir to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.feature_extractor import extract_features
from engine.score_fusion import compute_full_candidate_score
from engine.skill_confidence import compute_skill_confidence
from engine.ranker import compute_composite_rank_score
from engine.matcher import compute_match_breakdown
from signals.linkedin_signal import extract_linkedin_signals_from_resume, score_linkedin
from signals.github_signal import analyze_github_profile, score_github

def run_tests():
    print("==================================================")
    print("Starting HireIQ Intelligence Sprint Integration Tests")
    print("==================================================")

    # Test 1: Resume Text Feature Extraction
    print("\n[Test 1] Testing Resume Text Feature Extraction...")
    sample_resume = """
    Jane Doe
    jane.doe@example.com | +1 555-555-5555 | github.com/janedoe | linkedin.com/in/janedoe
    
    Summary:
    Experienced Software Engineer with 5 years of experience in backend development.

    Skills:
    Python, React, Go, TypeScript, SQL, Gin, PostgreSQL, Git, GitHub, AWS, Microservices
    
    Experience:
    Senior Software Engineer at Google | June 2021 - Present
    - Led a team of 4 engineers to design and deploy microservices.
    - Improved database query latency by 45% using PostgreSQL indexing.
    - Successfully launched the main billing sync.
    
    Education:
    B.Tech in Computer Science, IIT Bombay, 2017-2021
    
    Certifications:
    AWS Certified Solutions Architect Associate (AWS SAA)
    """
    
    features = extract_features(sample_resume)
    assert features["name"] == "Jane Doe", "Name extraction failed"
    assert features["email"] == "jane.doe@example.com", "Email extraction failed"
    assert features["phone"] == "+1 555-555-5555", "Phone extraction failed"
    assert features["education"] == "btech", f"Education extraction failed, got: {features['education']}"
    assert "AWS Certified Solutions Architect" in features["certifications"] or "AWS SAA" in features["certifications"], "Cert extraction failed"
    print("-> Test 1 Passed successfully!")

    # Test 2: GitHub Analysis
    print("\n[Test 2] Testing GitHub Profile Analysis & Verification...")
    mock_github_signals = {
        "account_age_years": 4.0,
        "total_repos": 15,
        "original_repos": 10,
        "total_stars": 80,
        "languages": ["Python", "JavaScript", "TypeScript"],
        "contribution_streak_estimate": 6,
        "commit_frequency_per_week": 8.0,
        "has_readme_ratio": 0.8,
        "has_tests": True,
        "top_repo_stars": 50,
        "open_source_prs_estimate": 4,
        "profile_completeness": 0.9,
    }
    
    claimed_skills = ["Python", "React", "Go", "TypeScript"]
    github_analysis = analyze_github_profile(mock_github_signals, claimed_skills, "backend")
    
    print(f"Engineering Score: {github_analysis['engineering_score']}")
    print(f"Verified Skills: {github_analysis['verified_skills']}")
    print(f"Unsupported Claims: {github_analysis['unsupported_claims']}")
    
    assert github_analysis["engineering_score"] > 60.0, "Engineering score calculation is wrong"
    assert "Python" in github_analysis["verified_skills"], "Verification failed"
    assert "Go" in github_analysis["unsupported_claims"], "Unsupported claim detection failed"
    print("-> Test 2 Passed successfully!")

    # Test 3: LinkedIn Signals & Verification
    print("\n[Test 3] Testing LinkedIn Signals & Inconsistency Checks...")
    linkedin_signals = extract_linkedin_signals_from_resume(sample_resume)
    assert linkedin_signals["has_linkedin"] is True, "LinkedIn detection failed"
    
    # Check score
    score = score_linkedin(linkedin_signals, "backend")
    print(f"LinkedIn Score: {score}")
    assert score > 0.5, "LinkedIn scoring is wrong"
    print("-> Test 3 Passed successfully!")

    # Test 4: Skill Confidence Model
    print("\n[Test 4] Testing Skill Confidence Model...")
    confidence_results = compute_skill_confidence(features, linkedin_signals, mock_github_signals)
    print("Skill Confidence List:")
    for skill, details in confidence_results.items():
        print(f"  - {skill}: {details['confidence']}% (Sources: {details['sources']})")
        
    assert "Python" in confidence_results, "Python not in confidence results"
    assert confidence_results["Python"]["confidence"] >= 75.0, "Python confidence score is too low"
    print("-> Test 4 Passed successfully!")

    # Test 5: Composite Ranking Score
    print("\n[Test 5] Testing Composite Ranking & Match Breakdown...")
    jd_features = {
        "required_skills": ["Python", "React", "PostgreSQL"],
        "preferred_skills": ["Go", "AWS"],
        "min_experience": 2,
        "max_experience": 10,
        "education_required": "btech"
    }
    
    base_scores = {
        "resume_skill_match": 0.85,
        "resume_experience": 0.90,
        "resume_education": 1.0,
    }
    
    signal_scores = {
        "github_score": github_analysis["engineering_score"] / 100.0,
        "linkedin_score": score,
        "portfolio_score": 0.7,
        "certification_score": 0.8,
    }
    
    all_scores = {**base_scores, **signal_scores}
    ranking_res = compute_composite_rank_score(all_scores, "Jane Doe", "backend_engineer")
    match_res = compute_match_breakdown(features, jd_features, github_analysis, linkedin_signals)
    
    print(f"Final Score: {ranking_res['final_score']}")
    print(f"Justification: {ranking_res['justification']}")
    print(f"Match Breakdown: {match_res}")
    
    assert ranking_res["final_score"] > 70.0, "Ranking score calculation failed"
    assert match_res["skills_match"] > 50.0, "Matcher calculation failed"
    print("-> Test 5 Passed successfully!")

    # Test 6: Complete Pipeline Orchestrator (compute_full_candidate_score)
    print("\n[Test 6] Testing Complete Pipeline Orchestrator...")
    import asyncio
    full_result = asyncio.run(compute_full_candidate_score(
        candidate_name="Jane Doe",
        resume_text=sample_resume,
        jd_features=jd_features,
        github_username="janedoe",
        role_type="backend_engineer"
    ))
    
    print(f"Complete Score: {full_result['final_score']}")
    print(f"AI Recruiter Summary Title: {full_result['insights']['ai_summary']['executive_summary'][:80]}...")
    assert full_result["final_score"] > 65.0, "Complete pipeline score failed"
    assert "insights" in full_result, "Insights dictionary missing from return value"
    print("-> Test 6 Passed successfully!")

    print("\n==================================================")
    print("All Integration Tests Passed Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
