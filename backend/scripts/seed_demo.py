import os
import uuid
import asyncio
import bcrypt
from dotenv import load_dotenv

# Ensure backend path is in sys.path
import sys
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Load env vars
load_dotenv()

from db import get_supabase
from db.supabase_client import save_candidate

async def seed():
    supabase = get_supabase()
    
    # 1. Create a demo recruiter
    email = "demo@hireiq.dev"
    company = "HireIQ Corp"
    
    # Check if exists
    res = supabase.table("recruiters").select("*").eq("email", email).execute()
    if res.data:
        recruiter = res.data[0]
        recruiter_id = recruiter["id"]
        print(f"Recruiter {email} already exists with ID: {recruiter_id}")
    else:
        recruiter_id = str(uuid.uuid4())
        hashed_password = bcrypt.hashpw("Demo1234!".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        recruiter = {
            "id": recruiter_id,
            "email": email,
            "hashed_password": hashed_password,
            "full_name": "Demo Admin",
            "company": company,
            "plan": "pro",
            "role": "Owner",
            "is_verified": True
        }
        supabase.table("recruiters").insert(recruiter).execute()
        print(f"Created demo recruiter: {email} with ID: {recruiter_id}")
        
    # 2. Create demo jobs
    jobs = [
        {
            "id": str(uuid.uuid4()),
            "title": "Senior Frontend Engineer",
            "description": "We need a strong frontend engineer to build scalable UI components using React, TypeScript, and Tailwind CSS.",
            "required_skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "CSS", "HTML", "Testing", "Webpack"],
            "min_experience": 3,
            "recruiter_id": recruiter_id
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Backend Python Developer",
            "description": "Backend developer for our core FastAPI backend, PostgreSQL database, Redis caching, and Docker containers.",
            "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "CI/CD"],
            "min_experience": 2,
            "recruiter_id": recruiter_id
        }
    ]
    
    for job in jobs:
        # Check if title exists
        j_res = supabase.table("jobs").select("*").eq("title", job["title"]).eq("recruiter_id", recruiter_id).execute()
        if not j_res.data:
            supabase.table("jobs").insert(job).execute()
            print(f"Created job: {job['title']}")
        else:
            print(f"Job {job['title']} already exists")
            
    # 3. Create demo candidates
    demo_candidates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Alice Chen",
            "email": "alice.chen@example.com",
            "role": "Senior Frontend Engineer",
            "github": "github.com/alicec",
            "linkedin": "linkedin.com/in/alicechen",
            "location": "San Francisco, CA",
            "score": 94,
            "blind_score": 96,
            "status": "Shortlisted",
            "summary": "Alice is a robust front-end specialist with a history of scaling design systems and optimizing web performance.",
            "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "CSS", "HTML", "Testing", "Webpack"],
            "experience": [{"title": "Senior UI Engineer", "company": "Vercel", "date": "2021-Present"}, {"title": "Frontend Developer", "company": "Stripe", "date": "2018-2021"}],
            "job_matches": [{"role": "Senior Frontend Engineer", "score": 94}],
            "radar_data": [{"subject": "React", "A": 95, "fullMark": 100}, {"subject": "TypeScript", "A": 90, "fullMark": 100}, {"subject": "Next.js", "A": 95, "fullMark": 100}, {"subject": "CSS/UI", "A": 92, "fullMark": 100}, {"subject": "Performance", "A": 88, "fullMark": 100}],
            "qa": [
                {"skill": "React", "question": "Explain React Server Components and their primary benefit.", "answer": "React Server Components run exclusively on the server. Their primary benefit is zero client-side bundle size for those components, faster initial loads, and direct backend resource access."},
                {"skill": "TypeScript", "question": "What is the difference between interface and type in TypeScript?", "answer": "Interfaces are open for declaration merging, whereas types cannot be re-declared. Types support unions, intersections, and mapped types, making them more expressive for complex types."}
            ],
            "insights": {
                "completeness_score": 95,
                "ats_score": 94,
                "strengths": ["Next.js/React architecture", "Design systems scaling", "Web Vitals optimization"],
                "weaknesses": ["Limited native mobile experience"],
                "concerns": []
            }
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Marcus Jones",
            "email": "marcus.j@example.com",
            "role": "Fullstack Engineer",
            "github": "github.com/mjones-dev",
            "linkedin": "linkedin.com/in/marcusj",
            "location": "Austin, TX",
            "score": 88,
            "blind_score": 85,
            "status": "Screening",
            "summary": "Marcus possesses a balanced full-stack skill set with deep proficiency in Node.js, Express, PostgreSQL, and React.",
            "skills": ["Node.js", "TypeScript", "React", "PostgreSQL", "Docker", "REST APIs", "SQL", "Redis"],
            "experience": [{"title": "Fullstack Developer", "company": "RetailCorp", "date": "2020-Present"}],
            "job_matches": [{"role": "Fullstack Developer", "score": 88}],
            "radar_data": [{"subject": "Node.js", "A": 90, "fullMark": 100}, {"subject": "React", "A": 85, "fullMark": 100}, {"subject": "Postgres", "A": 88, "fullMark": 100}, {"subject": "Docker", "A": 80, "fullMark": 100}, {"subject": "APIs", "A": 92, "fullMark": 100}],
            "qa": [
                {"skill": "Node.js", "question": "How does Node.js handle concurrency if it is single-threaded?", "answer": "Node.js uses an asynchronous event loop backed by a thread pool (libuv) for non-blocking I/O operations, offloading tasks like file systems and network requests."}
            ],
            "insights": {
                "completeness_score": 88,
                "ats_score": 88,
                "strengths": ["PostgreSQL schema design", "REST API development", "Docker containerization"],
                "weaknesses": ["Limited automated testing coverage"],
                "concerns": []
            }
        }
    ]
    
    # Fetch job list to link candidates
    job_list_res = supabase.table("jobs").select("*").eq("recruiter_id", recruiter_id).execute()
    jobs_dict = {j["title"]: j["id"] for j in job_list_res.data}
    
    for c in demo_candidates:
        c_res = supabase.table("candidates").select("id").eq("email", c["email"]).eq("recruiter_id", recruiter_id).execute()
        if not c_res.data:
            job_title = "Senior Frontend Engineer" if "Frontend" in c["role"] else "Backend Python Developer"
            if job_title in jobs_dict:
                c["jobMatches"] = [{"job_id": jobs_dict[job_title], "job_title": job_title, "tfidf_score": c["score"]}]
            await save_candidate(c, recruiter_id)
            print(f"Created candidate: {c['name']}")
        else:
            print(f"Candidate {c['name']} already exists")

if __name__ == "__main__":
    asyncio.run(seed())
