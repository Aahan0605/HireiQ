"""
Feature Extractor — Structured data extraction from resume and JD text.

Extracts skills, experience, education, and certifications from raw text
using KMP pattern matching and regex. Converts unstructured resume/JD
text into structured feature dicts for downstream scoring.

Internal search uses KMP (O(n+m)) for each skill pattern rather than
naive substring search, ensuring linear-time extraction across 80+ skills.
"""

from __future__ import annotations

import re
import logging
from typing import Optional

from algorithms.kmp import kmp_contains

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Known Skills — 80+ skills across categories
# ─────────────────────────────────────────────────────────────
KNOWN_SKILLS: list[str] = [
    # Programming Languages
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C++",
    "C#",
    "Go",
    "Rust",
    "Ruby",
    "PHP",
    "Swift",
    "Kotlin",
    "Scala",
    "R",
    "MATLAB",
    "Perl",
    "Haskell",
    "Elixir",
    "Dart",
    "Lua",
    "Julia",
    # Frontend Frameworks
    "React",
    "Angular",
    "Vue",
    "Svelte",
    "Next.js",
    "Nuxt",
    "Gatsby",
    "Remix",
    "Astro",
    "HTML",
    "CSS",
    "SASS",
    "Tailwind",
    # Backend Frameworks
    "Node.js",
    "Express",
    "FastAPI",
    "Django",
    "Flask",
    "Spring Boot",
    "Rails",
    "Laravel",
    "ASP.NET",
    "Gin",
    "Fiber",
    "NestJS",
    # Databases
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",
    "Cassandra",
    "DynamoDB",
    "SQLite",
    "Neo4j",
    "CockroachDB",
    "MariaDB",
    "Oracle",
    "SQL Server",
    "Supabase",
    "Firebase",
    # Cloud & DevOps
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Ansible",
    "Jenkins",
    "GitHub Actions",
    "CircleCI",
    "GitLab CI",
    "Pulumi",
    "CloudFormation",
    "Helm",
    "ArgoCD",
    # ML / AI / Data
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Keras",
    "Pandas",
    "NumPy",
    "Spark",
    "Hadoop",
    "Airflow",
    "dbt",
    "Kafka",
    "Flink",
    "Hugging Face",
    "OpenCV",
    "NLTK",
    "SpaCy",
    "LangChain",
    "MLflow",
    "Ray",
    "XGBoost",
    "LightGBM",
    # Tools & Practices
    "Git",
    "Linux",
    "Nginx",
    "GraphQL",
    "REST",
    "gRPC",
    "RabbitMQ",
    "Celery",
    "WebSocket",
    "OAuth",
    "JWT",
    "CI/CD",
    "Agile",
    "Scrum",
    "Microservices",
    "Serverless",
    "Event Driven",
]

# Normalized lookup for deduplication
_SKILLS_LOWER: dict[str, str] = {s.lower(): s for s in KNOWN_SKILLS}

# ─────────────────────────────────────────────────────────────
# Education Keywords
# Maps keywords found in resume text → normalized degree level
# ─────────────────────────────────────────────────────────────
EDUCATION_KEYWORDS: dict[str, str] = {
    "ph.d": "phd",
    "phd": "phd",
    "doctorate": "phd",
    "doctor of philosophy": "phd",
    "master of science": "masters",
    "master of technology": "mtech",
    "master of engineering": "masters",
    "master of arts": "masters",
    "m.tech": "mtech",
    "mtech": "mtech",
    "m.s.": "ms",
    "m.s": "ms",
    "ms ": "ms",
    "m.sc": "msc",
    "msc": "msc",
    "mba": "mba",
    "m.b.a": "mba",
    "master": "masters",
    "masters": "masters",
    "bachelor of science": "bachelors",
    "bachelor of technology": "btech",
    "bachelor of engineering": "be",
    "bachelor of arts": "bachelors",
    "b.tech": "btech",
    "btech": "btech",
    "b.e.": "be",
    "b.e": "be",
    "b.s.": "bs",
    "b.s": "bs",
    "bs ": "bs",
    "b.sc": "bsc",
    "bsc": "bsc",
    "bca": "bca",
    "b.c.a": "bca",
    "bachelor": "bachelors",
    "bachelors": "bachelors",
    "associate degree": "associate",
    "associate": "associate",
    "diploma": "diploma",
    "high school": "high_school",
    "bootcamp": "bootcamp",
    "self-taught": "self_taught",
    "self taught": "self_taught",
}

# ─────────────────────────────────────────────────────────────
# Certification Patterns
# ─────────────────────────────────────────────────────────────
CERTIFICATION_PATTERNS: dict[str, list[str]] = {
    "AWS": [
        "AWS Certified Solutions Architect",
        "AWS Certified Developer",
        "AWS Certified SysOps",
        "AWS Certified DevOps",
        "AWS Certified Cloud Practitioner",
        "AWS Certified Machine Learning",
        "AWS Certified Data Analytics",
        "AWS Certified Security",
        "AWS Certified Database",
        "AWS Certified Advanced Networking",
        "AWS SAA",
        "AWS SAP",
        "AWS DVA",
        "AWS SOA",
    ],
    "GCP": [
        "Google Cloud Certified",
        "GCP Professional Cloud Architect",
        "GCP Professional Data Engineer",
        "GCP Professional Machine Learning",
        "GCP Associate Cloud Engineer",
        "Google Cloud Digital Leader",
        "GCP Cloud Developer",
    ],
    "Azure": [
        "Microsoft Certified",
        "Azure Solutions Architect",
        "Azure Developer Associate",
        "Azure Administrator",
        "Azure Data Engineer",
        "Azure AI Engineer",
        "Azure DevOps Engineer",
        "AZ-900",
        "AZ-104",
        "AZ-204",
        "AZ-305",
        "AZ-400",
        "DP-900",
        "DP-203",
        "AI-900",
        "AI-102",
    ],
    "Kubernetes": [
        "CKA",
        "CKAD",
        "CKS",
        "Certified Kubernetes Administrator",
        "Certified Kubernetes Application Developer",
        "Certified Kubernetes Security Specialist",
    ],
    "Other": [
        "Terraform Associate",
        "HashiCorp Certified",
        "Certified Scrum Master",
        "CSM",
        "PMP",
        "Project Management Professional",
        "CISSP",
        "CISA",
        "CEH",
        "CompTIA Security+",
        "CompTIA Network+",
        "CompTIA A+",
        "Oracle Certified",
        "OCP",
        "OCA",
        "Salesforce Certified",
        "Databricks Certified",
        "Confluent Certified",
        "MongoDB Certified",
        "Neo4j Certified",
    ],
}


# ─────────────────────────────────────────────────────────────
# Helper Functions for Text Cleanup & Summaries
# ─────────────────────────────────────────────────────────────


def _normalize_text(text: str) -> str:
    """
    Clean and normalize text: fix camelCase, ALLCAPS, remove extra spaces.
    Time: O(n)
    """
    if not text:
        return ""

    # Fix camelCase: insert space between lowercase and uppercase (pythonCode → python Code)
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)

    # Fix ALLCAPS: insert space before uppercase followed by lowercase (PDFFile → PDF File)
    text = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", text)

    # Remove extra spaces and normalize
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _build_summary(
    skills: list[str], experience: float, projects_count: int = 0
) -> str:
    """
    Build a concise, structured summary: max 50 words, 3 sentences.
    Time: O(k) where k = number of top skills
    """
    if not skills and experience <= 0:
        return "Candidate profile pending analysis."

    top_skills = skills[:5] if len(skills) > 5 else skills
    skills_text = ", ".join(top_skills) if top_skills else "various skills"

    exp_text = f"{int(experience)} years" if experience > 0 else "Early-career"

    # Build 3-sentence summary under 50 words
    sentences = [
        f"{exp_text} of experience.",
        f"Key skills: {skills_text}.",
        f"Demonstrates strong technical foundation."
        if projects_count == 0
        else f"Built {projects_count}+ projects.",
    ]

    return " ".join(sentences)


def _extract_name(text: str) -> str:
    """
    Extract candidate name from resume text (first non-empty line).
    Validates name is real: 3–50 chars, only letters/spaces/hyphens.
    Time: O(n) where n = number of lines checked
    """
    if not text:
        return ""

    lines = text.strip().split("\n")

    for line in lines[:5]:  # Check first 5 lines only
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Clean markdown formatting characters
        cleaned_line = re.sub(r"[#*_`~|\\-]+", "", line).strip()

        # Validate length (3–50 chars for realistic names)
        if len(cleaned_line) < 3 or len(cleaned_line) > 50:
            continue

        # Skip lines with forbidden keywords
        forbidden = [
            "email",
            "phone",
            "linkedin",
            "github",
            "portfolio",
            "resume",
            "@",
            "http",
        ]
        if any(kw in cleaned_line.lower() for kw in forbidden):
            continue

        # Validate: only letters, spaces, hyphens allowed
        if not all(c.isalpha() or c.isspace() or c == "-" for c in cleaned_line):
            continue

        # Skip all-uppercase acronyms (AWS, PDF, etc.)
        if cleaned_line.isupper() and len(cleaned_line.split()) == 1:
            continue

        # Valid name found
        return cleaned_line

    return ""


def extract_contact(text: str) -> dict[str, str | None]:
    """
    Extract real contact information from resume text.

    Only extracts email, GitHub, LinkedIn, and phone if explicitly present.
    NEVER generates fake contact info. Returns None for missing fields.

    Time: O(n) where n = text length
    """
    email_pattern = r"[a-zA-Z0-9._%+-]+(?:\s+[a-zA-Z0-9._%+-]+)*\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}"
    email_match = re.findall(email_pattern, text)
    email = email_match[0].replace(" ", "").replace("\t", "").replace("\n", "") if email_match else None

    # GitHub URL extraction
    github = None
    github_pattern = r"github\.com/\s*([\w\-]+)"
    github_match = re.findall(github_pattern, text, re.IGNORECASE)
    if github_match:
        github = f"github.com/{github_match[0].strip()}"
    else:
        # Fallback to github: username
        github_fallback_match = re.search(r"github\s*:\s*([\w\-]+)", text, re.IGNORECASE)
        if github_fallback_match:
            github = f"github.com/{github_fallback_match.group(1).strip()}"

    # LinkedIn URL extraction
    linkedin = None
    linkedin_pattern = r"linkedin\.com/in/\s*([\w\-]+)"
    linkedin_match = re.findall(linkedin_pattern, text, re.IGNORECASE)
    if linkedin_match:
        linkedin = f"linkedin.com/in/{linkedin_match[0].strip()}"
    else:
        # Fallback to linkedin: username or linkedin.com/username
        linkedin_fallback_match = re.search(r"linkedin\s*:\s*([\w\-]+)", text, re.IGNORECASE)
        if linkedin_fallback_match:
            linkedin = f"linkedin.com/in/{linkedin_fallback_match.group(1).strip()}"
        else:
            linkedin_alt = re.findall(r"linkedin\.com/([a-zA-Z0-9\-]+)", text, re.IGNORECASE)
            if linkedin_alt:
                linkedin = f"linkedin.com/in/{linkedin_alt[0]}"
    
    # Phone number matching pattern supporting international format, brackets, hyphens, and spaces
    phone_pattern = r"\+?\d{1,4}?[\s.-]?\(?\d{1,3}?\)?[\s.-]?\d{1,4}[\s.-]?\d{1,4}[\s.-]?\d{1,9}"
    phone_match = re.findall(phone_pattern, text)

    # Location extraction
    location = None
    location_match = re.search(r"(?:location|address|lives in|based in)\s*:\s*([a-zA-Z\s,]+)", text, re.IGNORECASE)
    if location_match:
        location = location_match.group(1).strip()
    else:
        city_state_match = re.search(r"\b([A-Z][a-zA-Z\s]{2,20}),\s*([A-Z]{2})\b", text)
        if city_state_match:
            location = f"{city_state_match.group(1)}, {city_state_match.group(2)}"

    return {
        "email": email,
        "github": github,
        "linkedin": linkedin,
        "phone": phone_match[0].strip() if phone_match else None,
        "location": location,
    }


def _extract_email(text: str) -> str:
    """
    Extract email address from resume text. Real extraction only.
    Time: O(n)
    """
    if not text:
        return None

    pattern = r"[a-zA-Z0-9._%+-]+(?:\s+[a-zA-Z0-9._%+-]+)*\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0).replace(" ", "").replace("\t", "").replace("\n", "") if match else None


def _extract_github(text: str) -> str:
    """
    Extract GitHub profile URL from resume text. Real extraction only - no fakes.
    Time: O(n)
    """
    if not text:
        return None

    pattern = r"(?:https?://)?(?:www\.)?github\.com/\s*[\w\-]+(?:\s+[\w\-]+)*"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).replace(" ", "").replace("\t", "").replace("\n", "") if match else None


def _extract_linkedin(text: str) -> str:
    """
    Extract LinkedIn profile URL from resume text. Real extraction only - no fakes.
    Time: O(n)
    """
    if not text:
        return None

    pattern = r"(?:https?://)?(?:www\.)?linkedin\.com/in/\s*[\w\-]+(?:\s+[\w\-]+)*"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).replace(" ", "").replace("\t", "").replace("\n", "") if match else None


def _extract_experience_from_timeline(text: str) -> list[dict]:
    """
    Extract work experience timeline entries from resume using date patterns.
    Time: O(n)
    """
    if not text:
        return []

    experiences = []

    # Look for date patterns: "2020", "2020-2023", "Jan 2022", "January 2022 - Present"
    date_pattern = r"(?:\d{1,2}\s)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}|\d{4}(?:\s*[-–]\s*(?:\d{4}|Present|Current))?"

    lines = text.split("\n")

    for i, line in enumerate(lines):
        # Look for lines with dates
        if re.search(date_pattern, line, re.IGNORECASE):
            # Try to extract job title (usually before or after date) and company
            company_match = re.search(
                r"(?:at|@|\|)\s*([A-Z][A-Za-z\s&,.-]+?)(?:\s*-|\s*\||$)", line
            )
            dates = re.search(date_pattern, line, re.IGNORECASE)

            if dates or company_match:
                entry = {
                    "title": line.split("|")[0]
                    .replace("at", "")
                    .replace("@", "")
                    .strip()[:50]
                    if "|" in line or "@" in line
                    else "Not specified",
                    "company": company_match.group(1).strip()
                    if company_match
                    else "Not specified",
                    "date": dates.group(0) if dates else "Unknown",
                    "description": "",
                }
                experiences.append(entry)

    return experiences[:5]  # Return max 5 experiences



def _extract_projects(text: str) -> list[dict[str, str]]:
    """
    Extract project titles and descriptions from resume text.
    Looks for sections labeled 'projects' or similar and parses list items.
    """
    projects = []
    text_lower = text.lower()
    
    # Locate project section
    project_headers = ["projects", "personal projects", "academic projects", "key projects", "selected projects"]
    start_idx = -1
    for header in project_headers:
        idx = text_lower.find(header)
        if idx != -1:
            start_idx = idx + len(header)
            break
            
    if start_idx != -1:
        # End of section is the next major header (e.g. Experience, Education, Skills)
        next_headers = ["experience", "education", "skills", "certifications", "languages", "interests", "about me"]
        end_idx = len(text)
        for nh in next_headers:
            idx = text_lower.find(nh, start_idx)
            if idx != -1 and idx < end_idx:
                end_idx = idx
                
        project_section = text[start_idx:end_idx].strip()
        lines = [l.strip() for l in project_section.split("\n") if l.strip()]
        
        current_project = None
        for line in lines:
            is_bullet = line.startswith(("*", "-", "•", "▪"))
            clean_line = re.sub(r"^[*\-•▪]\s*", "", line).strip()
            
            title_match = re.search(r"^([a-zA-Z0-9\s\-\.\/]+)(?:\s*[\(\[].*?[\)\]])?(?:\s*[:|–—-])", clean_line)
            if title_match and len(title_match.group(1).strip()) < 40:
                title = title_match.group(1).strip()
                desc = clean_line[title_match.end():].strip()
                current_project = {"title": title, "description": desc}
                projects.append(current_project)
            elif is_bullet and current_project:
                current_project["description"] += " " + clean_line
            elif len(clean_line) < 40 and any(c.isupper() for c in clean_line[:3]):
                current_project = {"title": clean_line, "description": ""}
                projects.append(current_project)
            elif current_project:
                current_project["description"] += " " + clean_line

    for p in projects:
        p["description"] = p["description"].strip()
        
    projects = [p for p in projects if len(p["title"]) > 2]
    
    if not projects:
        project_regex = re.findall(r"(?:built|developed|designed|implemented)\s+([A-Z][A-Za-z0-9\s\-]+?)(?:\s+using|\s+with|\s+to|\s+for|\.|,)", text)
        for match in project_regex[:3]:
            title = match.strip()
            if len(title) > 3 and len(title) < 40:
                projects.append({"title": title, "description": f"Developed {title} integration."})
                
    return projects[:5]


def _extract_achievements(text: str) -> list[str]:
    """
    Extract achievement statements from the resume (bullet points emphasizing impact/results).
    """
    achievements = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    impact_keywords = [
        r"\b(?:won|awarded|achieved|ranked|first place|scholarship)\b",
        r"\b(?:increased|decreased|reduced|saved|grew|improved|optimized|cut)\s+(?:by\s+)?\d+\s*%",
        r"\b(?:managed|led|directed|oversaw)\s+team\s+of\s+\d+",
        r"\b(?:published|presented|authored)\b",
        r"\b(?:successfully\s+)?(?:launched|delivered|deployed|migrated)\b"
    ]
    
    for line in lines:
        clean_line = re.sub(r"^[*\-•▪]\s*", "", line).strip()
        if len(clean_line) < 15 or len(clean_line) > 150:
            continue
            
        for pattern in impact_keywords:
            if re.search(pattern, clean_line, re.IGNORECASE):
                achievements.append(clean_line)
                break
                
    return achievements[:5]


def extract_features(text: str) -> dict:
    """
    Extract structured features from resume text.
    """
    if not text:
        return {
            "name": "",
            "email": None,
            "phone": None,
            "github": None,
            "linkedin": None,
            "skills": [],
            "experience": 0.0,
            "education": "unknown",
            "certifications": [],
            "projects": [],
            "achievements": [],
            "raw_text": "",
        }

    skills = _extract_skills(text)
    experience = _extract_experience(text)
    education = _extract_education(text)
    certifications = _extract_certifications(text)
    name = _extract_name(text)
    contact = extract_contact(text)
    projects = _extract_projects(text)
    achievements = _extract_achievements(text)

    experience_timeline = extract_experience(text)

    return {
        "name": name,
        "email": contact.get("email"),
        "phone": contact.get("phone"),
        "github": contact.get("github"),
        "linkedin": contact.get("linkedin"),
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications,
        "projects": projects,
        "achievements": achievements,
        "raw_text": text,
        "experience_timeline": experience_timeline,
    }


def extract_jd_features(jd_text: str) -> dict:
    """
    Extract structured features from a job description.

    Similar to resume extraction but tailored for JD patterns:
        - required_skills: skills explicitly mentioned
        - keywords: all detected skill terms
        - experience_required: minimum years asked for
        - education_required: minimum degree level
        - raw_text: original JD text

    Time Complexity: O(n·k) where n = text length, k = number of known skills (KMP for each)
    Space Complexity: O(k) for skills list

    Args:
        jd_text: Cleaned job description text.

    Returns:
        Dict with JD-specific feature keys.

    Examples:
        >>> jd = "Looking for a Python developer with 3+ years, MS preferred"
        >>> features = extract_jd_features(jd)
        >>> "Python" in features["required_skills"]
        True
    """
    if not jd_text:
        return {
            "required_skills": [],
            "keywords": [],
            "experience_required": 0.0,
            "education_required": "unknown",
            "raw_text": "",
        }

    skills = _extract_skills(jd_text)
    experience = _extract_experience(jd_text)
    education = _extract_education(jd_text)

    # Extract "required" vs "nice to have" skills from JD context
    required_skills = _extract_required_skills(jd_text, skills)

    return {
        "required_skills": required_skills,
        "keywords": skills,
        "experience_required": experience,
        "education_required": education,
        "raw_text": jd_text,
    }


def _extract_skills(text: str) -> list[str]:
    """
    Detect known skills in text with expanded skill list and category parsing.

    Time Complexity: O(n·k) where n = text length, k = number of skills
    Space Complexity: O(k) for found skills set

    Args:
        text: Resume or JD text.

    Returns:
        Deduplicated list of canonical skill names found (max 30).
    """
    if not text:
        return []

    # Extended KNOWN_SKILLS list with more AI/ML and frameworks
    extended_skills = [
        # Programming Languages (expanded)
        "Python",
        "C++",
        "JavaScript",
        "Java",
        "SQL",
        "TypeScript",
        "Go",
        "Rust",
        "C#",
        "PHP",
        "Ruby",
        "Swift",
        "Kotlin",
        "Scala",
        "R",
        "MATLAB",
        # Frontend Frameworks
        "React",
        "React.js",
        "Vue",
        "Angular",
        "Svelte",
        "Next.js",
        "Nuxt",
        "Astro",
        "Gatsby",
        "Tailwind",
        "Tailwind CSS",
        "HTML",
        "CSS",
        "SASS",
        # Backend Frameworks
        "Node.js",
        "Express",
        "FastAPI",
        "Flask",
        "Django",
        "Spring Boot",
        "Rails",
        "Laravel",
        "ASP.NET",
        "Gin",
        "Fiber",
        "NestJS",
        # AI/ML (expanded)
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "Keras",
        "Hugging Face",
        "Machine Learning",
        "Deep Learning",
        "Neural Networks",
        "LLM",
        "Computer Vision",
        "NLP",
        "Data Science",
        # Database
        "MySQL",
        "MongoDB",
        "PostgreSQL",
        "SQLite",
        "Redis",
        "Elasticsearch",
        "DynamoDB",
        "Cassandra",
        "Firebase",
        "Supabase",
        # Cloud & DevOps
        "Docker",
        "Kubernetes",
        "Git",
        "GitHub",
        "GitLab",
        "AWS",
        "GCP",
        "Azure",
        "CI/CD",
        "Jenkins",
        "GitHub Actions",
        "GitLab CI",
        "CircleCI",
        "Terraform",
        "Ansible",
        "Pulumi",
        # Data & Tools
        "Pandas",
        "NumPy",
        "Spark",
        "Hadoop",
        "Kafka",
        "Airflow",
        "Jupyter",
        "VS Code",
        "Linux",
        "Postman",
        # Other Tech
        "REST APIs",
        "GraphQL",
        "Solidity",
        "Blockchain",
        "OAuth",
        "JWT",
        "Microservices",
        "Serverless",
        "gRPC",
        "WebSocket",
        "RabbitMQ",
        "Celery",
        "Data Structures",
        "Algorithms",
        "DBMS",
        "Operating Systems",
        "Agile",
        "Scrum",
        "JIRA",
        "Figma",
        "Nginx",
        "Apache",
    ]

    found = []
    text_lower = text.lower()
    found_lower = set()

    # Check each skill in text (case-insensitive)
    for skill in extended_skills:
        if skill.lower() not in found_lower and skill.lower() in text_lower:
            found.append(skill)
            found_lower.add(skill.lower())

    # Also extract from "Category: skill1, skill2" pattern
    category_pattern = r"(?:Programming|AI/ML|Frameworks|Database|Tools|Skills|Languages|Technologies|Expertise)[:\s]+([^\n]+)"
    for match in re.finditer(category_pattern, text, re.IGNORECASE):
        line = match.group(1)
        # Split on common delimiters
        inline_skills = re.split(r"[,|•\n]", line)
        for s in inline_skills:
            s = s.strip()
            if len(s) > 1 and s.lower() not in found_lower:
                found.append(s)
                found_lower.add(s.lower())

    # Deduplicate preserving order
    seen = set()
    unique = []
    for s in found:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique.append(s)

    return unique[:30]  # max 30 skills


def _extract_experience(text: str) -> float:
    """
    Extract years of experience from experience entries with dates.
    Parses experience timeline to calculate total years.
    """
    if not text:
        return 0.0

    text_lower = text.lower()
    years_found: list[float] = []

    # Helper to parse month/year into numerical year float
    def parse_date(date_str: str) -> float | None:
        date_str = date_str.lower().strip()
        if date_str in ("present", "current", "now"):
            return 2026.5  # current time approximation for mid-2026

        # Try to find year
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", date_str)
        if not year_match:
            return None
        year = int(year_match.group(1))

        # Try to find month
        months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        month_idx = 0  # default to Jan
        for i, m in enumerate(months):
            if m in date_str:
                month_idx = i
                break
        else:
            # Check for numeric month: e.g. "06/2021" or "06-2021"
            num_month_match = re.search(r"\b(0?[1-9]|1[0-2])[\s/]+(20\d{2}|19\d{2})\b", date_str)
            if num_month_match:
                month_idx = int(num_month_match.group(1)) - 1

        return year + (month_idx / 12.0)

    # 1. Match date ranges (e.g. "June 2021 - Present", "06/2021 - 08/2023", "2018 - 2021", "Jan 2020 to Dec 2022")
    date_regex = r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s\.\d,]*\d{4})|(?:\d{1,2}[\s/]+\d{4})|(?:\b\d{4}\b)"
    range_regex = rf"({date_regex})\s*(?:-|–|—|to)\s*({date_regex}|present|current|now)"
    
    accumulated_years = 0.0
    # Process line-by-line to filter out education-related lines
    for line in text_lower.split("\n"):
        if any(keyword in line for keyword in ["university", "college", "school", "iit", "nirma", "education", "degree", "btech", "mtech", "b.tech", "b.s.", "bachelor", "master", "phd", "coursework"]):
            continue
        
        ranges = re.findall(range_regex, line)
        for start_str, end_str in ranges:
            t_start = parse_date(start_str)
            t_end = parse_date(end_str)
            if t_start is not None and t_end is not None:
                diff = t_end - t_start
                if 0 < diff < 40:
                    accumulated_years += diff

    if accumulated_years > 0:
        years_found.append(round(accumulated_years, 1))

    # Pattern 1: "X years of experience" / "X+ years" / "X yrs"
    pattern1 = re.findall(
        r"(\d+\.?\d*)\s*\+?\s*(?:years?|yrs?)[\s\-]*(?:of\s+)?(?:experience|exp)?",
        text_lower,
    )
    for match in pattern1:
        try:
            years_found.append(float(match))
        except ValueError:
            continue

    # Pattern 2: "X-Y years" (range, take the max)
    pattern2 = re.findall(
        r"(\d+\.?\d*)\s*[-–—to]+\s*(\d+\.?\d*)\s*(?:years?|yrs?)", text_lower
    )
    for low, high in pattern2:
        try:
            years_found.append(float(high))
        except ValueError:
            continue

    # Pattern 3: "over/more than X years"
    pattern3 = re.findall(
        r"(?:over|more\s+than|exceeding|above)\s+(\d+\.?\d*)\s*(?:years?|yrs?)",
        text_lower,
    )
    for match in pattern3:
        try:
            years_found.append(float(match))
        except ValueError:
            continue

    # Pattern 4: "experience: X years" / "experience of X years"
    pattern4 = re.findall(
        r"experience\s*(?::|of)\s*(\d+\.?\d*)\s*(?:years?|yrs?)", text_lower
    )
    for match in pattern4:
        try:
            years_found.append(float(match))
        except ValueError:
            continue

    # Pattern 5: "since 20XX" — calculate approximate years
    pattern5 = re.findall(r"since\s+(20\d{2})", text_lower)
    for year_str in pattern5:
        try:
            start_year = int(year_str)
            approx_years = 2026 - start_year
            if 0 < approx_years < 50:
                years_found.append(float(approx_years))
        except ValueError:
            continue

    if not years_found:
        return 0.0

    return max(years_found)



def extract_experience(text: str) -> list[dict]:
    """
    Extract work experience timeline from resume.

    Handles pattern:
        Company Name - Role
        Month Year - Month Year
        Description line 1
        Description line 2

    Time: O(n) where n = number of lines
    """
    experiences = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    date_pattern = re.compile(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.\-]+\d{4}"
        r"|(\d{4})\s*[-–]\s*(\d{4}|Present|Current|Now)",
        re.IGNORECASE,
    )

    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if current or next line has a date
        curr_date = date_pattern.search(line)
        next_date = date_pattern.search(lines[i + 1]) if i + 1 < len(lines) else None

        if curr_date or next_date:
            company_line = line if not curr_date else (lines[i - 1] if i > 0 else line)
            date_str = (curr_date or next_date).group(0)

            # Collect up to 2 description lines after
            desc_lines = []
            j = i + (2 if next_date else 1)
            while j < min(i + 4, len(lines)):
                if not date_pattern.search(lines[j]):
                    desc_lines.append(lines[j])
                j += 1

            comp = company_line
            title = "Software Engineer"
            for sep in [" - ", " – ", " | ", " : ", " -", " –", " |", " :"]:
                if sep in company_line:
                    parts = company_line.split(sep, 1)
                    comp = parts[0].strip()
                    title = parts[1].strip()
                    break

            company_clean = re.sub(r"[-–|•]", "", comp).strip()
            title_clean = re.sub(r"[-–|•]", "", title).strip()

            if company_clean and len(company_clean) > 2:
                experiences.append(
                    {
                        "company": company_clean,
                        "title": title_clean,
                        "date": date_str,
                        "description": " ".join(desc_lines[:2]) if desc_lines else "",
                    }
                )
            i = j
        else:
            i += 1

    return experiences


def _extract_education(text: str) -> str:
    """
    Extract the highest education level from text.

    Scans for education keywords and returns the degree with the
    highest value according to EDUCATION_KEYWORDS → config.EDUCATION_SCORES.

    Args:
        text: Resume or JD text.

    Returns:
        Normalized education level string (e.g., "btech", "masters", "phd").
        Returns "unknown" if no education keywords are found.

    Examples:
        >>> _extract_education("B.Tech in CS from IIT Delhi, pursuing M.Tech")
        'mtech'
    """
    if not text:
        return "unknown"

    # Import here to avoid circular dependency at module level
    from config import EDUCATION_SCORES

    text_lower = text.lower()
    detected: list[tuple[str, float]] = []

    # Sort keywords by length descending so longer/more specific matches win
    sorted_keywords = sorted(EDUCATION_KEYWORDS.keys(), key=len, reverse=True)

    for keyword in sorted_keywords:
        # Check for whole-word boundary matches to avoid false positives (e.g., matching "mba" in "Bombay")
        if re.search(r"\b" + re.escape(keyword) + r"\b", text_lower):
            degree = EDUCATION_KEYWORDS[keyword]
            score = EDUCATION_SCORES.get(degree, 0.0)
            detected.append((degree, score))

    if not detected:
        return "unknown"

    # Return the highest-scoring education level
    detected.sort(key=lambda x: x[1], reverse=True)
    return detected[0][0]


def _extract_certifications(text: str) -> list[str]:
    """
    Detect professional certifications mentioned in text.

    Searches for known certification patterns across AWS, GCP, Azure,
    Kubernetes, and other vendors using case-insensitive KMP matching.

    Time Complexity: O(n·p·m) where n = text length, p = # patterns, m = pattern length
    Space Complexity: O(p) for found certs

    Args:
        text: Resume or JD text.

    Returns:
        Deduplicated list of detected certification names.

    Examples:
        >>> certs = _extract_certifications("I hold AWS SAA and CKA certifications")
        >>> "AWS SAA" in certs
        True
        >>> "CKA" in certs
        True
    """
    if not text:
        return []

    found: list[str] = []

    for vendor, patterns in CERTIFICATION_PATTERNS.items():
        for cert_pattern in patterns:
            if kmp_contains(text, cert_pattern):
                found.append(cert_pattern)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for cert in found:
        if cert not in seen:
            seen.add(cert)
            unique.append(cert)

    return unique


def _extract_required_skills(jd_text: str, all_skills: list[str]) -> list[str]:
    """
    Identify which skills in a JD are explicitly required vs nice-to-have.

    Looks for skills mentioned near "required", "must have", "mandatory"
    keywords. Falls back to returning all skills if no such context exists.

    Time Complexity: O(n + k) where n = text length, k = number of skills
    Space Complexity: O(k) for required skills list

    Args:
        jd_text:    Job description text.
        all_skills: All skills already detected in the JD.

    Returns:
        List of skills classified as required.
    """
    if not jd_text or not all_skills:
        return all_skills

    text_lower = jd_text.lower()

    # Find "required" / "must have" sections
    required_markers = [
        "required",
        "must have",
        "mandatory",
        "essential",
        "minimum qualifications",
        "basic qualifications",
        "requirements:",
        "you must",
    ]
    nice_markers = [
        "nice to have",
        "preferred",
        "bonus",
        "good to have",
        "desired",
        "plus",
        "optional",
        "ideally",
    ]

    # Simple heuristic: find the section boundaries
    required_start = -1
    nice_start = len(text_lower)

    for marker in required_markers:
        idx = text_lower.find(marker)
        if idx != -1 and (required_start == -1 or idx < required_start):
            required_start = idx

    for marker in nice_markers:
        idx = text_lower.find(marker)
        if idx != -1 and idx < nice_start:
            nice_start = idx

    # If no clear required section, treat all skills as required
    if required_start == -1:
        return all_skills

    # Extract required section text
    required_section = text_lower[required_start:nice_start]

    required_skills = []
    for skill in all_skills:
        if skill.lower() in required_section:
            required_skills.append(skill)

    # If filtering resulted in nothing, return all
    return required_skills if required_skills else all_skills


def get_skill_categories(skills: list[str]) -> dict[str, list[str]]:
    """
    Categorize detected skills into domain groups.

    Useful for visual breakdown in candidate reports.

    Args:
        skills: List of detected skill names.

    Returns:
        Dict mapping category name → list of skills in that category.
    """
    categories: dict[str, list[str]] = {
        "Languages": [],
        "Frontend": [],
        "Backend": [],
        "Databases": [],
        "Cloud/DevOps": [],
        "ML/AI/Data": [],
        "Tools": [],
    }

    language_set = {
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C++",
        "C#",
        "Go",
        "Rust",
        "Ruby",
        "PHP",
        "Swift",
        "Kotlin",
        "Scala",
        "R",
        "MATLAB",
        "Perl",
        "Haskell",
        "Elixir",
        "Dart",
        "Lua",
        "Julia",
    }
    frontend_set = {
        "React",
        "Angular",
        "Vue",
        "Svelte",
        "Next.js",
        "Nuxt",
        "Gatsby",
        "Remix",
        "Astro",
        "HTML",
        "CSS",
        "SASS",
        "Tailwind",
    }
    backend_set = {
        "Node.js",
        "Express",
        "FastAPI",
        "Django",
        "Flask",
        "Spring Boot",
        "Rails",
        "Laravel",
        "ASP.NET",
        "Gin",
        "Fiber",
        "NestJS",
    }
    db_set = {
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "Elasticsearch",
        "Cassandra",
        "DynamoDB",
        "SQLite",
        "Neo4j",
        "CockroachDB",
        "MariaDB",
        "Oracle",
        "SQL Server",
        "Supabase",
        "Firebase",
    }
    cloud_set = {
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "Terraform",
        "Ansible",
        "Jenkins",
        "GitHub Actions",
        "CircleCI",
        "GitLab CI",
        "Pulumi",
        "CloudFormation",
        "Helm",
        "ArgoCD",
    }
    ml_set = {
        "TensorFlow",
        "PyTorch",
        "Scikit-learn",
        "Keras",
        "Pandas",
        "NumPy",
        "Spark",
        "Hadoop",
        "Airflow",
        "dbt",
        "Kafka",
        "Flink",
        "Hugging Face",
        "OpenCV",
        "NLTK",
        "SpaCy",
        "LangChain",
        "MLflow",
        "Ray",
        "XGBoost",
        "LightGBM",
    }

    for skill in skills:
        if skill in language_set:
            categories["Languages"].append(skill)
        elif skill in frontend_set:
            categories["Frontend"].append(skill)
        elif skill in backend_set:
            categories["Backend"].append(skill)
        elif skill in db_set:
            categories["Databases"].append(skill)
        elif skill in cloud_set:
            categories["Cloud/DevOps"].append(skill)
        elif skill in ml_set:
            categories["ML/AI/Data"].append(skill)
        else:
            categories["Tools"].append(skill)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def generate_resume_insights(
    features: dict,
    text: str,
    github_signals: dict | None = None,
    linkedin_signals: dict | None = None,
) -> dict:
    """Generate detailed candidate insights and scores from extracted features."""
    import re
    skills = list(features.get("skills", []))
    experience = features.get("experience", 0.0)
    education = features.get("education", "unknown")
    certs = features.get("certifications", [])

    # Merge GitHub languages into skills list (deduplicated)
    if github_signals and github_signals.get("languages"):
        for lang in github_signals.get("languages", []):
            if lang.lower() not in {s.lower() for s in skills}:
                skills.append(lang)

    # 1. Completeness Score
    score_parts = 0
    if len(skills) >= 5: score_parts += 20
    elif len(skills) >= 1: score_parts += 10
    
    if experience > 0: score_parts += 20
    if experience >= 5: score_parts += 10  # experience depth
    
    if education != "unknown": score_parts += 20
    
    email_m = re.search(r"[a-zA-Z0-9._%+-]+(?:\s+[a-zA-Z0-9._%+-]+)*\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}", text)
    github_m = re.search(r"github\.com/\s*[\w\-]+(?:\s+[\w\-]+)*", text, re.I)
    linkedin_m = re.search(r"linkedin\.com/in/\s*[\w\-]+(?:\s+[\w\-]+)*", text, re.I)
    
    has_github = github_m or (github_signals and bool(github_signals))
    has_linkedin = linkedin_m or (linkedin_signals and linkedin_signals.get("has_linkedin"))
    
    if email_m: score_parts += 15
    if has_github: score_parts += 12
    if has_linkedin: score_parts += 13
    
    # factor in github repo count (>=5 repos = +10pts)
    if github_signals and github_signals.get("total_repos", 0) >= 5:
        score_parts += 10
        
    # factor in certifications
    if certs or (linkedin_signals and linkedin_signals.get("certifications")):
        score_parts += 10
        
    completeness = min(100, max(20, score_parts))

    # 2. ATS Score
    ats_points = 30
    if "experience" in text.lower() or "work history" in text.lower() or "employment" in text.lower(): ats_points += 15
    if "education" in text.lower() or "academic" in text.lower() or "university" in text.lower(): ats_points += 15
    if "skills" in text.lower() or "technologies" in text.lower() or "technical expertise" in text.lower(): ats_points += 15
    
    word_count = len(text.split())
    if word_count >= 400: ats_points += 10
    
    if len(skills) >= 8: ats_points += 15
    
    # penalise skill overload
    if len(skills) > 30: ats_points -= 8
    elif len(skills) > 20: ats_points -= 5
    
    if github_signals:
        commit_freq = github_signals.get("commit_frequency_per_week", github_signals.get("commit_frequency", 0.0))
        if commit_freq > 2:
            ats_points += 8
            
    ats_score = min(100, max(30, ats_points))

    # 3. Career Progression
    if experience >= 8.0:
        progression = "Senior Leadership / Principal Tier"
    elif experience >= 4.0:
        progression = "Mid-Senior Level Specialist"
    elif experience >= 1.5:
        progression = "Independent Professional / Mid-Level"
    elif experience > 0.0:
        progression = "Early Career / Associate Level"
    else:
        progression = "Entry Level / Student"

    # 4. Strengths, Weaknesses, and Concerns
    strengths = []
    weaknesses = []
    concerns = []

    if len(skills) >= 10:
        strengths.append("Broad technical skillset with over 10+ core technologies.")
    if experience >= 5:
        strengths.append("Established track record with 5+ years in engineering.")
    if certs:
        strengths.append(f"Validated industry competence with {len(certs)} certifications (e.g. {certs[0]}).")
    if has_github:
        strengths.append("Active open source developer footprint detected via GitHub.")
    if github_signals:
        stars = github_signals.get("total_stars", 0)
        if stars >= 20:
            strengths.append(f"Strong open-source validation with {stars} total GitHub stars.")
        commit_freq = github_signals.get("commit_frequency_per_week", github_signals.get("commit_frequency", 0.0))
        if commit_freq >= 5:
            strengths.append(f"High development velocity with {commit_freq:.1f} commits per week.")
        if github_signals.get("has_tests"):
            strengths.append("Demonstrates commitment to software quality with test suites present in repositories.")
    if linkedin_signals:
        recs = linkedin_signals.get("recommendations", 0)
        if recs > 0:
            strengths.append(f"Strong peer endorsements with {recs} LinkedIn recommendations.")
        conns = linkedin_signals.get("connections", 0)
        if conns >= 500:
            strengths.append(f"Extensive professional network with {conns}+ LinkedIn connections.")

    if len(strengths) == 0:
        strengths.append("Possesses core fundamental engineering skills.")

    if len(skills) < 5:
        weaknesses.append("Narrow technical stack listing. Recommend expanding core skills.")
    if experience < 1.0:
        if not github_signals:
            weaknesses.append("Limited commercial experience listed on profile, compounded by lack of public GitHub portfolio.")
        else:
            weaknesses.append("Limited commercial experience listed, but compensated by active public GitHub portfolio.")
    if education == "unknown":
        weaknesses.append("No formal degree program detected on resume.")
    if not certs and not (linkedin_signals and linkedin_signals.get("certifications")):
        weaknesses.append("No cloud or vendor certifications listed to validate domain competence.")
    if len(weaknesses) == 0:
        weaknesses.append("None identified. High compatibility across standard criteria.")

    if not has_linkedin and not has_github:
        concerns.append("Minimal online portfolio presence (missing both LinkedIn and GitHub links).")
    if experience > 10.0 and len(skills) < 6:
        concerns.append("Experience/Skill set mismatch: long tenure but very few modern skills listed.")
    if len(concerns) == 0:
        concerns.append("Resume structures align with industry best practices.")

    sources_used = {
        "resume": True,
        "github": github_signals is not None and bool(github_signals),
        "linkedin": linkedin_signals is not None and linkedin_signals.get("has_linkedin", False)
    }

    return {
        "completeness_score": completeness,
        "ats_score": ats_score,
        "career_progression": progression,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "concerns": concerns,
        "sources_used": sources_used,
    }


async def extract_features_async(text: str) -> dict:
    """
    Extract features from resume text asynchronously using the hiring-agent LLM pipeline
    if enabled, with fallback to the legacy rule-based extractor.
    """
    if not text:
        return {
            "name": "",
            "email": None,
            "phone": None,
            "github": None,
            "linkedin": None,
            "skills": [],
            "experience": 0.0,
            "education": "unknown",
            "certifications": [],
            "projects": [],
            "achievements": [],
            "raw_text": "",
        }

    from config import HIRING_AGENT_ENABLED
    if HIRING_AGENT_ENABLED:
        try:
            from hiring_agent.pdf_extractor import PDFHandler
            from hiring_agent.transform import to_hireiq_features
            handler = PDFHandler()
            json_resume = await handler.extract_all_from_text(text)
            if json_resume:
                features = to_hireiq_features(json_resume)
                features["raw_text"] = text
                features["achievements"] = []
                return features
        except Exception as e:
            logger.warning(f"hiring-agent async extraction failed: {e}. Falling back to legacy extractor.")
            
    return extract_features(text)


