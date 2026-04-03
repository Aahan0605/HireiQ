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


def _extract_name(text: str) -> str:
    """
    Extract candidate name from resume text (first non-empty line or main heading).
    Time: O(n)
    """
    if not text:
        return ""

    lines = text.strip().split("\n")
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and len(line) > 2 and len(line) < 100:
            # Filter out common headers/footers
            if not any(
                keyword in line.lower()
                for keyword in [
                    "email",
                    "phone",
                    "linkedin",
                    "github",
                    "portfolio",
                    "resume",
                ]
            ):
                return line

    return ""


def _extract_email(text: str) -> str:
    """
    Extract email address from resume text.
    Time: O(n)
    """
    if not text:
        return ""

    # Improved email regex
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else ""


def _extract_github(text: str) -> str:
    """
    Extract GitHub profile URL from resume text.
    Time: O(n)
    """
    if not text:
        return ""

    # Look for github.com pattern
    match = re.search(
        r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text, re.IGNORECASE
    )
    if match:
        return match.group(0)

    # Fallback: look for just github username after @ or /
    match = re.search(r"github[:\s/]*(\w+)", text, re.IGNORECASE)
    if match:
        return f"github.com/{match.group(1)}"

    return ""


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
    Detect known skills in text using KMP string matching.

    Uses case-insensitive KMP search for each known skill pattern.
    Returns canonical skill names (properly cased) for matched skills.

    Handles multi-word skills (e.g., "GitHub Actions", "Spring Boot")
    and tech variants (e.g., "node.js", "Node", "NodeJS" all → "Node.js").

    Args:
        text: Resume or JD text.

    Returns:
        Deduplicated list of canonical skill names found, sorted alphabetically.
    """
    if not text:
        return []

    found: set[str] = set()
    text_lower = text.lower()

    # Variant mapping: common alternate spellings → canonical name
    variants: dict[str, str] = {
        "nodejs": "Node.js",
        "node js": "Node.js",
        "node.js": "Node.js",
        "reactjs": "React",
        "react.js": "React",
        "react js": "React",
        "vuejs": "Vue",
        "vue.js": "Vue",
        "angularjs": "Angular",
        "angular.js": "Angular",
        "nextjs": "Next.js",
        "next.js": "Next.js",
        "nuxtjs": "Nuxt",
        "nuxt.js": "Nuxt",
        "nestjs": "NestJS",
        "nest.js": "NestJS",
        "expressjs": "Express",
        "express.js": "Express",
        "fastapi": "FastAPI",
        "fast api": "FastAPI",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "dynamodb": "DynamoDB",
        "dynamo db": "DynamoDB",
        "elasticsearch": "Elasticsearch",
        "elastic search": "Elasticsearch",
        "scikit-learn": "Scikit-learn",
        "scikit learn": "Scikit-learn",
        "sklearn": "Scikit-learn",
        "tensorflow": "TensorFlow",
        "tf ": "TensorFlow",
        "pytorch": "PyTorch",
        "torch": "PyTorch",
        "hugging face": "Hugging Face",
        "huggingface": "Hugging Face",
        "langchain": "LangChain",
        "lang chain": "LangChain",
        "github actions": "GitHub Actions",
        "gh actions": "GitHub Actions",
        "gitlab ci": "GitLab CI",
        "gitlab-ci": "GitLab CI",
        "circleci": "CircleCI",
        "circle ci": "CircleCI",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "c++": "C++",
        "cplusplus": "C++",
        "c#": "C#",
        "csharp": "C#",
        "asp.net": "ASP.NET",
        "aspnet": "ASP.NET",
        "spring boot": "Spring Boot",
        "springboot": "Spring Boot",
        "tailwindcss": "Tailwind",
        "tailwind css": "Tailwind",
        "tailwind": "Tailwind",
        "graphql": "GraphQL",
        "graph ql": "GraphQL",
        "rabbitmq": "RabbitMQ",
        "rabbit mq": "RabbitMQ",
        "websocket": "WebSocket",
        "web socket": "WebSocket",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "light gbm": "LightGBM",
    }

    # Check canonical skills via KMP
    for skill in KNOWN_SKILLS:
        if kmp_contains(text, skill):
            found.add(skill)

    # Check variant spellings
    for variant, canonical in variants.items():
        if kmp_contains(text, variant):
            found.add(canonical)

    return sorted(found)


def _extract_experience(text: str) -> float:
    """
    Extract years of experience from text using regex patterns.

    Matches patterns like:
        - "5 years of experience"
        - "3+ years experience"
        - "5-7 years"
        - "over 10 years"
        - "2.5 years"
        - "experience: 4 years"

    Returns the maximum years value found (assumes candidates state
    their total/highest experience). Returns 0.0 if no match.

    Args:
        text: Resume or JD text.

    Returns:
        Estimated years of experience as float.

    Examples:
        >>> _extract_experience("I have 5+ years of software development experience")
        5.0
        >>> _extract_experience("3-5 years required")
        5.0
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
