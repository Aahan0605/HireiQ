import os
import sys
import zipfile
import urllib.request
import uuid
import random
from pathlib import Path
from dotenv import load_dotenv

# Add parent dir to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load env
load_dotenv()

from db.session import SessionLocal
from db.models import User, OrganizationMember, Candidate
from db.supabase_client import save_candidate
from api.core.rbac import tenant_context

# Target URL for the dataset
ZIP_URL = "https://github.com/florex/resume_corpus/archive/refs/heads/master.zip"
TEMP_DIR = Path("/Users/aahanajaygajera/Desktop/al&ml/hireiq/backend/scratch/temp_resumes")
TEMP_DIR.mkdir(parents=True, exist_ok=True)
ZIP_PATH = TEMP_DIR / "repo.zip"

def download_and_extract():
    # If we already have numeric txt files in TEMP_DIR, we can skip
    existing_txts = list(TEMP_DIR.glob("[0-9]*.txt")) or list(TEMP_DIR.glob("**/[0-9]*.txt"))
    if len(existing_txts) >= 25:
        print("Dataset already downloaded and extracted. Skipping download.")
        return

    import ssl
    print(f"Downloading repository from {ZIP_URL}...")
    context = ssl._create_unverified_context()
    with urllib.request.urlopen(ZIP_URL, context=context) as response, open(ZIP_PATH, 'wb') as out_file:
        out_file.write(response.read())
    print("Extracting repository ZIP...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)
    
    # Now look for resumes_corpus.zip inside the extracted repo
    sample_zip_path = None
    for p in TEMP_DIR.glob("**/resumes_corpus.zip") or TEMP_DIR.glob("**/resume*.zip"):
        sample_zip_path = p
        break
        
    if not sample_zip_path:
        raise FileNotFoundError("Could not find resumes_corpus.zip inside the extracted repository.")
        
    print(f"Extracting sample dataset zip: {sample_zip_path}...")
    with zipfile.ZipFile(sample_zip_path, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)
    print("Extraction completed.")

def parse_resumes():
    # Find all numeric .txt files in TEMP_DIR
    txt_files = sorted(list(TEMP_DIR.glob("[0-9]*.txt")))
    if not txt_files:
        # Fallback to look deeper if nested
        txt_files = sorted(list(TEMP_DIR.glob("**/[0-9]*.txt")))
        
    if not txt_files:
        raise FileNotFoundError(f"Could not find any numeric resume text files in {TEMP_DIR}")
        
    print(f"Found {len(txt_files)} numeric resume files. Parsing the first 25...")
    
    resumes = []
    for txt_file in txt_files[:25]:
        # Corresponding lab file
        lab_file = txt_file.with_suffix('.lab')
        
        # Parse occupations/role from lab file
        occupations = []
        if lab_file.exists():
            with open(lab_file, 'r', encoding='utf-8', errors='ignore') as lf:
                for line in lf:
                    parts = line.strip().split(';')
                    for part in parts:
                        cleaned = part.replace('_', ' ').strip()
                        if cleaned:
                            occupations.append(cleaned)
                            
        # If no role, fallback to "Software Engineer"
        if not occupations:
            occupations = ["Software Engineer"]
            
        # Read resume text
        with open(txt_file, 'r', encoding='utf-8', errors='ignore') as tf:
            text = tf.read().strip()
            
        # Clean HTML highlights from the text
        text_clean = text.replace('<span class="hl">', '').replace('</span>', '')
        
        resumes.append({
            "ref_id": txt_file.stem,
            "occupations": occupations,
            "text": text_clean
        })
        
    print(f"Successfully parsed {len(resumes)} resumes.")
    return resumes

# Realistic names and locations to make candidate profiles premium
NAMES = [
    "Alex Rivera", "Jordan Smith", "Taylor Chen", "Morgan Vance", "Casey Albright",
    "Jamie Patel", "Skyler Thorne", "Riley Cooper", "Robin Hayes", "Avery Brooks",
    "Drew Sterling", "Peyton Vance", "Quinn Hadley", "Logan Avery", "Cameron Blake",
    "Hayden Cole", "Parker Chase", "Dakota Reed", "Dallas Vance", "Emerson Cross",
    "Finley Hayes", "Phoenix Brooks", "Rowan Thorne", "Sage Sterling", "Tatum Hadley",
    "Eden Avery", "Reese Blake", "Sawyer Cole", "Micah Chase", "Ellis Reed"
]

LOCATIONS = [
    "New York, NY", "San Francisco, CA", "Seattle, WA", "Austin, TX", "Boston, MA",
    "Chicago, IL", "Denver, CO", "Atlanta, GA", "Los Angeles, CA", "Miami, FL"
]

SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "Django", "PostgreSQL",
    "Docker", "Kubernetes", "AWS", "FastAPI", "Go", "Redis", "CI/CD", "Git"
]

async def add_candidates_to_db():
    download_and_extract()
    resumes = parse_resumes()
    
    # We will pick 25 resumes to add
    to_add = resumes[:25]
    
    db = SessionLocal()
    try:
        # Find default user REDACTED_EMAIL@example.com
        user = db.query(User).filter(User.email == "REDACTED_EMAIL@example.com").first()
        if not user:
            print("Default admin user not found in database. Seed user first.")
            return
            
        # Get user's active tenant
        member = db.query(OrganizationMember).filter(OrganizationMember.user_id == user.id).first()
        if not member:
            print("Default organization membership not found.")
            return
            
        tenant_id = member.organization_id
        # Set tenant context
        tenant_context.set(tenant_id)
        print(f"Adding resumes to Tenant Workspace: {tenant_id}")
        
        for i, res in enumerate(to_add):
            name = NAMES[i % len(NAMES)]
            email = f"{name.lower().replace(' ', '.')}@example.com"
            location = random.choice(LOCATIONS)
            
            # Basic analysis parameters
            score = random.randint(65, 98)
            blind_score = score + random.randint(-2, 3)
            blind_score = min(100, max(0, blind_score))
            
            # Map occupations to roles
            role = res["occupations"][0] if res["occupations"] else "Software Engineer"
            role = role.title()
            
            # Get skills found in text or randomly assign
            skills = [s for s in SKILLS_POOL if s.lower() in res["text"].lower()]
            if not skills:
                skills = random.sample(SKILLS_POOL, random.randint(3, 6))
                
            experience = []
            if len(res["text"]) > 200:
                experience.append({"title": role, "company": "TechCorp", "date": "2022-Present"})
                experience.append({"title": "Junior Developer", "company": "Software Solutions", "date": "2020-2022"})
            else:
                experience.append({"title": role, "company": "Web Development LLC", "date": "2021-Present"})
                
            # Radar data for Recharts
            radar_data = []
            for s in skills[:5]:
                radar_data.append({"subject": s, "A": random.randint(60, 95), "fullMark": 100})
            while len(radar_data) < 5:
                radar_data.append({"subject": f"Skill {len(radar_data)}", "A": random.randint(60, 95), "fullMark": 100})
                
            candidate_payload = {
                "id": str(uuid.uuid4()),
                "organization_id": tenant_id,
                "name": name,
                "email": email,
                "role": role,
                "github": f"github.com/{name.lower().replace(' ', '')}",
                "linkedin": f"linkedin.com/in/{name.lower().replace(' ', '')}",
                "location": location,
                "score": score,
                "blind_score": blind_score,
                "status": random.choice(["Screening", "Shortlisted", "Interviewing"]),
                "summary": res["text"][:250].replace('\n', ' ') + "...",
                "skills": skills,
                "experience": experience,
                "job_matches": [{"role": role, "score": score}],
                "radar_data": radar_data,
                "qa": [
                    {"skill": skills[0] if skills else "General", "question": "What is your typical approach to troubleshooting?", "answer": "I systematically isolate the module, look at logs, reproduce the issue locally, and resolve it."}
                ],
                "insights": {
                    "completeness_score": random.randint(75, 95),
                    "ats_score": score,
                    "career_progression": "Steady growth",
                    "strengths": ["Demonstrates technical capacity", "Understands core programming principles"],
                    "weaknesses": ["Needs more deep system design exposure"],
                    "concerns": []
                }
            }
            
            await save_candidate(candidate_payload)
            print(f"Added Candidate {i+1}/{len(to_add)}: {name} ({role})")
            
        print(f"Successfully added {len(to_add)} candidates from online resume dataset to website!")
        
        # Clean up temp files
        print("Cleaning up temporary resume files...")
        import shutil
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        print("Cleanup completed.")
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(add_candidates_to_db())
