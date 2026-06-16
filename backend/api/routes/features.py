import uuid
import logging
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from api.core.rbac import require_tenant
from db import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/features", tags=["Roadmap Features"], dependencies=[Depends(require_tenant)])

# ─── Pydantic Request Models ────────────────────────────────────

class LinkedInImportRequest(BaseModel):
    linkedin_url: str
    job_id: Optional[str] = None

class CopilotGenerateRequest(BaseModel):
    candidate_id: str
    type: str  # "outreach", "rejection", "offer", "notes"
    job_title: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class InterviewSimulateRequest(BaseModel):
    candidate_id: str
    messages: List[ChatMessage]

# ─── Mock Sourcing Data Helper ──────────────────────────────────

MOCK_DISCOVERED = [
    {"name": "Sarah Jenkins", "headline": "Staff Backend Engineer at Netflix", "skills": ["Python", "FastAPI", "AWS", "Kubernetes"], "location": "Austin, TX", "github": "github.com/sjenkins", "experience": 8},
    {"name": "Marcus Aurelio", "headline": "Senior Frontend Developer at Stripe", "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS"], "location": "Miami, FL", "github": "github.com/marcusaur", "experience": 6},
    {"name": "Elena Rostova", "headline": "Machine Learning Engineer at OpenAI", "skills": ["Python", "PyTorch", "Transformers", "LLMs"], "location": "San Francisco, CA", "github": "github.com/erostova", "experience": 5},
    {"name": "David Kim", "headline": "Lead Systems Architect at HashiCorp", "skills": ["Go", "Terraform", "Docker", "Consul"], "location": "Seattle, WA", "github": "github.com/dkim-systems", "experience": 10},
    {"name": "Priya Sharma", "headline": "Full Stack Engineer at Figma", "skills": ["React", "Node.js", "TypeScript", "PostgreSQL"], "location": "New York, NY", "github": "github.com/priyas", "experience": 4}
]

# ─── Routes Implementation ──────────────────────────────────────

@router.post("/linkedin-import")
async def import_linkedin(req: LinkedInImportRequest, tenant_id: str = Depends(require_tenant)):
    """Simulate importing a candidate profile directly from a LinkedIn URL."""
    url = req.linkedin_url.strip().lower()
    if "linkedin.com/in/" not in url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid LinkedIn profile URL (e.g. linkedin.com/in/username)"
        )
        
    # Extract username or mock
    username = url.split("linkedin.com/in/")[-1].split("/")[0] or "candidate"
    name = username.replace("-", " ").replace(".", " ").title()
    email = f"{username.replace('.', '')}@example.com"
    
    candidate_id = str(uuid.uuid4())
    supabase = get_supabase()
    
    # Generate high fidelity candidate profile details
    skills = ["React", "TypeScript", "Node.js", "Tailwind CSS", "PostgreSQL"] if "front" in name.lower() or "design" in name.lower() else ["Python", "FastAPI", "Docker", "PostgreSQL", "AWS"]
    career_tier = "Senior Software Engineer" if "sr" in name.lower() or "senior" in name.lower() else "Software Engineer"
    
    db_record = {
        "id": candidate_id,
        "recruiter_id": tenant_id,
        "full_name": name,
        "email": email,
        "phone": "+1 (555) 019-2834",
        "location": "San Francisco, CA (Hybrid)",
        "experience_years": 5,
        "education_tier": "bachelors",
        "skills": skills,
        "raw_text": f"LinkedIn imported profile of {name}. Experince in software engineering.",
        "match_score": 88,
        "completeness_score": 90,
        "ats_score": 85,
        "career_tier": career_tier,
        "key_strengths": ["Strong architectural design", "Highly collaborative team player"],
        "development_gaps": ["Could gain more cloud ops experience"],
        "potential_concerns": [],
        "pipeline_stage": "screening",
        "github_url": f"github.com/{username}",
        "github_stars": 12,
        "github_languages": ["Python", "TypeScript"],
        "github_commits_last_year": 140,
        "blind_score": 89,
        "resume_filename": f"{username}_linkedin.pdf",
        "interview_questions": [],
        "insights": {
            "linkedin": url,
            "resume_base64": "",
            "match_breakdown": {
                "overall_match_percentage": 88,
                "skills_match": 90,
                "experience_match": 85,
                "education_match": 80,
                "projects_match": 75,
                "github_match": 80
            }
        },
        "summary": f"{name} is a highly accomplished {career_tier} with verified experience imported directly from LinkedIn."
    }
    
    if req.job_id:
        try:
            db_record["job_id"] = req.job_id
        except Exception:
            pass
            
    try:
        supabase.table("candidates").insert(db_record).execute()
    except Exception as e:
        logger.error(f"Error creating candidate from LinkedIn import: {e}")
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")
        
    return {"status": "success", "candidate_id": candidate_id, "name": name, "email": email}

@router.post("/copilot/generate")
async def copilot_generate(req: CopilotGenerateRequest):
    """Generate dynamic recruitment copy using candidate profiles."""
    supabase = get_supabase()
    res = supabase.table("candidates").select("*").eq("id", req.candidate_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Candidate not found")
    candidate = res.data[0]
    
    name = candidate.get("full_name", "Candidate")
    role = req.job_title or candidate.get("career_tier", "Software Engineer")
    skills_list = ", ".join(candidate.get("skills", [])[:3])
    
    if req.type == "outreach":
        subject = f"Exciting Opportunity at HireIQ Corp: {role}"
        body = (
            f"Hi {name.split(' ')[0]},\n\n"
            f"I came across your profile and was extremely impressed by your background in engineering, "
            f"particularly your hands-on experience with {skills_list}.\n\n"
            f"We are currently hiring a {role} at HireIQ Corp, and we think your technical expertise aligns "
            f"exceptionally well with our core roadmap goals. I'd love to hop on a quick 15-minute call "
            f"this week to share more about our engineering challenges and learn about your career interests.\n\n"
            f"Do you have some availability this Thursday afternoon?\n\n"
            f"Best regards,\n"
            f"The HireIQ Recruiting Team"
        )
    elif req.type == "rejection":
        subject = f"Your application for the {role} role at HireIQ Corp"
        body = (
            f"Dear {name},\n\n"
            f"Thank you for taking the time to interview with us and share your background in {skills_list}.\n\n"
            f"While our team was impressed with your technical capabilities, we have decided to move forward "
            f"with other candidates whose experience more closely matches our immediate infrastructure requirements "
            f"for the {role} position.\n\n"
            f"We will keep your profile in our talent network for future openings that may align with your skills. "
            f"We wish you the best of luck in your job search.\n\n"
            f"Sincerely,\n"
            f"HireIQ Recruiting"
        )
    elif req.type == "offer":
        subject = f"Official Offer of Employment: {role} - HireIQ Corp"
        body = (
            f"Dear {name},\n\n"
            f"On behalf of HireIQ Corp, we are thrilled to offer you the position of {role}.\n\n"
            f"We were incredibly impressed by your interviews, particularly your deep understanding of system scaling "
            f"and proficiency in {skills_list}. We are confident that you will make a huge impact on our team.\n\n"
            f"Key details of our offer:\n"
            f"• Position: {role}\n"
            f"• Compensation: $145,000 USD Annual Base Salary\n"
            f"• Equity: 15,000 Options\n"
            f"• Benefits: Full health, dental, vision, and unlimited PTO\n\n"
            f"Please sign and return the attached offer letter within 5 business days to confirm your acceptance.\n\n"
            f"Welcome to the team!\n\n"
            f"Best,\n"
            f"The HireIQ Executive Board"
        )
    else: # notes
        subject = f"Recruiter Summary Notes: {name}"
        body = (
            f"=== INTERNAL RECRUITER NOTES ===\n"
            f"Candidate: {name}\n"
            f"Target Role: {role}\n"
            f"Technical Strengths: Highly skilled in {skills_list}. Solid GitHub activity with positive code quality indicators.\n"
            f"Communication: Clear articulation of architectural decisions. Active listening.\n"
            f"Hiring Verdict: Strong recommendation to advance to deep technical evaluations. Candidate exhibits strong growth potential."
        )
        
    return {"subject": subject, "body": body}

@router.post("/interview/simulate")
async def interview_simulate(req: InterviewSimulateRequest):
    """Simulate an AI-driven adaptive screening interview."""
    msg_count = len(req.messages)
    
    supabase = get_supabase()
    res = supabase.table("candidates").select("*").eq("id", req.candidate_id).execute()
    candidate = res.data[0] if res.data else {}
    name = candidate.get("full_name", "Candidate")
    skills = candidate.get("skills", ["Python", "FastAPI"])
    
    # Adaptive question logic based on progress
    if msg_count == 0:
        reply = f"Hello {name}! Thank you for joining our first-round technical screening. To start, could you tell me about a complex project you worked on recently using {skills[0]}?"
        done = False
        scorecard = None
    elif msg_count == 1:
        reply = "That sounds fascinating. How did you design the database schema and handle concurrency or scalability challenges in that system?"
        done = False
        scorecard = None
    elif msg_count == 2:
        reply = f"Excellent. One final question: if you had to optimize a slow API endpoint querying thousands of records using {skills[0]}, what steps would you take?"
        done = False
        scorecard = None
    else:
        reply = "Thank you so much for your thorough responses! I have captured your technical capabilities. Our recruiting team will review the details and reach out shortly."
        done = True
        scorecard = {
            "problem_solving": 92,
            "technical_depth": 88,
            "communication": 90,
            "overall_recommendation": "Strong Hire",
            "notes": f"{name} demonstrated clear mastery in {skills[0]} optimization, system design heuristics, and solid clean code habits."
        }
        
    return {"reply": reply, "is_completed": done, "scorecard": scorecard}

@router.get("/security/audit-logs")
async def get_audit_logs(tenant_id: str = Depends(require_tenant)):
    """Generate and export a CSV file containing security audit logs."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["Timestamp", "IP Address", "User ID", "Event Type", "Resource Affected", "Status"])
    
    # Generate mock audit logs
    base_time = datetime.utcnow()
    logs = [
        [base_time - timedelta(minutes=5), "192.168.1.101", tenant_id, "USER_LOGIN", "Authentication Router", "SUCCESS"],
        [base_time - timedelta(minutes=12), "192.168.1.101", tenant_id, "EXPORT_DATA", "Candidates Table CSV", "SUCCESS"],
        [base_time - timedelta(hours=1), "192.168.1.101", tenant_id, "UPDATE_WEIGHTS", "Algorithm Weights", "SUCCESS"],
        [base_time - timedelta(hours=2, minutes=15), "10.0.0.4", "system-cron", "AUTOMATED_COMPLIANCE_SWEEP", "GDPR Pruning Job", "SUCCESS"],
        [base_time - timedelta(days=1, hours=3), "192.168.1.101", tenant_id, "INVITE_MEMBER", "Recruiter (hiring-manager@hireiq.dev)", "SUCCESS"],
        [base_time - timedelta(days=2), "192.168.1.105", "unknown-ip", "SSO_CONFIG_ATTEMPT", "SAML SSO Endpoint", "FAILED"]
    ]
    
    for log in logs:
        writer.writerow([log[0].isoformat(), log[1], log[2], log[3], log[4], log[5]])
        
    output.seek(0)
    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=hireiq_audit_logs.csv"
    return response

@router.get("/analytics/executive")
async def get_executive_analytics():
    """Return mock executive metrics and funnel conversion data."""
    return {
        "time_to_hire": 18.5,  # days
        "cost_per_hire": 3250.0,  # USD
        "funnel_conversion": 4.2,  # % conversion from application to hire
        "offer_acceptance": 88.0,  # % acceptance rate
        "conversion_stages": [
            {"stage": "Applied", "count": 1200},
            {"stage": "Screening", "count": 480},
            {"stage": "Interviewing", "count": 120},
            {"stage": "Offer", "count": 25},
            {"stage": "Hired", "count": 22}
        ],
        "monthly_hiring": [
            {"month": "Jan", "hires": 3},
            {"month": "Feb", "hires": 5},
            {"month": "Mar", "hires": 4},
            {"month": "Apr", "hires": 8},
            {"month": "May", "hires": 6},
            {"month": "Jun", "hires": 9}
        ]
    }

@router.get("/analytics/workforce")
async def get_workforce_planning():
    """Return mock workforce planning skill shortages and forecasts."""
    return {
        "skill_shortages": [
            {"skill": "Kubernetes", "gap_percentage": 65, "status": "Critical"},
            {"skill": "React", "gap_percentage": 20, "status": "Stable"},
            {"skill": "Go/Golang", "gap_percentage": 45, "status": "Moderate"},
            {"skill": "FastAPI", "gap_percentage": 10, "status": "Low"}
        ],
        "demand_forecast": [
            {"quarter": "Q3-26", "demand": 14},
            {"quarter": "Q4-26", "demand": 18},
            {"quarter": "Q1-27", "demand": 25},
            {"quarter": "Q2-27", "demand": 30}
        ]
    }

@router.get("/outreach/discover")
async def discover_outreach(query: Optional[str] = None):
    """Filter mock public talent profiles matching open roles."""
    if not query:
        return MOCK_DISCOVERED
        
    query_lower = query.lower()
    filtered = []
    for candidate in MOCK_DISCOVERED:
        match = (
            query_lower in candidate["name"].lower() or
            query_lower in candidate["headline"].lower() or
            any(query_lower in s.lower() for s in candidate["skills"])
        )
        if match:
            filtered.append(candidate)
    return filtered
