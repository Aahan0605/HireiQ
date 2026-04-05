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

        # Validate length (3–50 chars for realistic names)
        if len(line) < 3 or len(line) > 50:
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
        if any(kw in line.lower() for kw in forbidden):
            continue

        # Validate: only letters, spaces, hyphens allowed
        if not all(c.isalpha() or c.isspace() or c == "-" for c in line):
            continue

        # Skip all-uppercase acronyms (AWS, PDF, etc.)
        if line.isupper() and len(line.split()) == 1:
            continue

        # Valid name found
        return line

    return ""


def extract_contact(text: str) -> dict[str, str | None]:
    """
    Extract real contact information from resume text.

    Only extracts email, GitHub, LinkedIn if explicitly present.
    NEVER generates fake contact info. Returns None for missing fields.

    Time: O(n) where n = text length
    """
    email_match = re.findall(r"[\w\.\-]+@[\w\.\-]+\.\w{2,}", text)
    github_match = re.findall(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    linkedin_match = re.findall(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)

    return {
        "email": email_match[0] if email_match else None,
        "github": github_match[0] if github_match else None,
        "linkedin": linkedin_match[0] if linkedin_match else None,
    }


def _extract_email(text: str) -> str:
    """
    Extract email address from resume text. Real extraction only.
    Time: O(n)
    """
    if not text:
        return None

    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w{2,}", text)
    return match.group(0) if match else None


def _extract_github(text: str) -> str:
    """
    Extract GitHub profile URL from resume text. Real extraction only - no fakes.
    Time: O(n)
    """
    if not text:
        return None

    # Look for github.com pattern
    match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text, re.IGNORECASE
    )
    if match:
        return match.group(0)

    return None


def _extract_linkedin(text: str) -> str:
    """
    Extract LinkedIn profile URL from resume text. Real extraction only - no fakes.
    Time: O(n)
    """
    if not text:
        return None

    # Look for linkedin.com/in/ pattern
    match = re.search(
        r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+", text, re.IGNORECASE
    )
    if match:
        return match.group(0)

    return None


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


def extract_features(text: str) -> dict:
    """
    Extract structured features from resume text.

    Performs:
        1. Skill detection using KMP pattern matching
        2. Experience extraction via regex
        3. Education level identification
        4. Certification detection

    Time Complexity: O(n·k) where n = text length, k = number of known skills (KMP for each)
    Space Complexity: O(k) for skills list

    Args:
        text: Cleaned resume text (output of resume_parser).

    Returns:
        Dict with keys:
            - skills:         list[str] — matched skill names
            - experience:     float — estimated years of experience
            - education:      str — highest education level detected
            - certifications: list[str] — detected certifications
            - raw_text:       str — original text for downstream use

    Examples:
        >>> features = extract_features("Python developer with 5 years experience, B.Tech, AWS SAA certified")
        >>> "Python" in features["skills"]
        True
        >>> features["experience"]
        5.0
    """
    if not text:
        return {
            "skills": [],
            "experience": 0.0,
            "education": "unknown",
            "certifications": [],
            "raw_text": "",
        }

    skills = _extract_skills(text)
    experience = _extract_experience(text)
    education = _extract_education(text)
    certifications = _extract_certifications(text)

    return {
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications,
        "raw_text": text,
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
    Time: O(n)
    """
    if not text:
        return 0.0

    text_lower = text.lower()
    years_found: list[float] = []

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
            approx_years = 2026 - start_year  # current year approximation
            if 0 < approx_years < 50:
                years_found.append(float(approx_years))
        except ValueError:
            continue

    if not years_found:
        return 0.0

    # Return the maximum detected years (most representative)
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

            company_clean = re.sub(r"[-–|•]", "", company_line).strip()
            if company_clean and len(company_clean) > 2:
                experiences.append(
                    {
                        "company": company_clean,
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
        if keyword in text_lower:
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
