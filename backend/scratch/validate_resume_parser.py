import os
import sys
from pathlib import Path

# Add parent dir to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.feature_extractor import extract_features

def test_resume_parser():
    print("Starting Resume Parser Validation...")
    
    # 1. Developer Resume Mock
    dev_resume = """
    Jane Doe
    Email: jane.doe@example.com | Phone: +1-555-0199-283 | GitHub: github.com/janedoe | LinkedIn: linkedin.com/in/janedoe
    
    Professional Summary:
    Experienced Software Engineer with a focus on building scalable web applications.
    
    Skills:
    Python, Django, FastAPI, React, TypeScript, AWS, Docker, Kubernetes, SQL, Git
    
    Experience:
    Senior Software Engineer @ TechCorp | June 2022 - Present
    - Led a team of 4 engineers to rebuild the core ingestion pipeline.
    - Improved data processing efficiency by 35% using Celery and Redis.
    - Successfully launched the new billing integration on time.
    
    Software Engineer @ WebStart | Jan 2020 - May 2022
    - Developed and maintained multiple React and TypeScript micro-frontends.
    - Reduced page load times by 1.2s through code-splitting and asset optimization.
    
    Projects:
    E-Commerce Microservices:
    - Designed and implemented a microservices-based shop backend using FastAPI and PostgreSQL.
    - Dockerized all services and deployed to AWS ECS.
    
    Personal Portfolio Website:
    - Created a serverless portfolio with Astro and Tailwind, hosted on Vercel.
    
    Education:
    B.Tech in Computer Science and Engineering, IIT Bombay | 2016 - 2020
    
    Certifications:
    AWS Certified Solutions Architect (AWS SAA), Certified Kubernetes Administrator (CKA)
    """

    features = extract_features(dev_resume)
    
    print("\n--- Extracted Features ---")
    print(f"Name: {features['name']}")
    print(f"Email: {features['email']}")
    print(f"Phone: {features['phone']}")
    print(f"GitHub: {features['github']}")
    print(f"LinkedIn: {features['linkedin']}")
    print(f"Skills: {features['skills']}")
    print(f"Experience: {features['experience']} years")
    print(f"Education: {features['education']}")
    print(f"Certifications: {features['certifications']}")
    print(f"Projects count: {len(features['projects'])}")
    for p in features['projects']:
        print(f"  - Project: {p['title']} -> {p['description'][:60]}...")
    print(f"Achievements count: {len(features['achievements'])}")
    for a in features['achievements']:
        print(f"  - Achievement: {a}")

    # Assertions to ensure our parser works correctly
    assert features["email"] == "jane.doe@example.com", "Email extraction failed"
    assert features["phone"] == "+1-555-0199-283", "Phone extraction failed"
    assert "github.com/janedoe" in features["github"], "GitHub extraction failed"
    assert "linkedin.com/in/janedoe" in features["linkedin"], "LinkedIn extraction failed"
    assert "Python" in features["skills"], "Skills extraction failed (Python)"
    assert "React" in features["skills"], "Skills extraction failed (React)"
    assert features["education"] == "btech", f"Education extraction failed, got: {features['education']}"
    assert "AWS Certified Solutions Architect" in features["certifications"] or "AWS SAA" in features["certifications"], "Certifications extraction failed"
    assert len(features["projects"]) >= 2, "Projects extraction failed"
    assert len(features["achievements"]) >= 2, "Achievements extraction failed"
    
    print("\nResume Parser Validation Passed successfully!")

if __name__ == "__main__":
    test_resume_parser()
