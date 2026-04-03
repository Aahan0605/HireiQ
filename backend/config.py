"""
HireIQ Configuration — Scoring weights, role profiles, and evaluation thresholds.

All weights across SCORING_WEIGHTS must sum to 1.0.
Role-specific profiles override base weights for targeted evaluation.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────
# Base Scoring Weights (must sum to 1.0)
# ─────────────────────────────────────────────────────────────
SCORING_WEIGHTS: dict[str, float] = {
    "resume_skill_match":   0.15,
    "resume_experience":    0.08,
    "resume_education":     0.05,
    "github_score":         0.15,
    "competitive_coding":   0.12,
    "portfolio_score":      0.08,
    "linkedin_score":       0.08,
    "stackoverflow_score":  0.04,
    "certification_score":  0.07,
    "research_score":       0.03,
    "live_test_score":      0.10,
    "video_score":          0.03,
    "reference_score":      0.02,
}

assert abs(sum(SCORING_WEIGHTS.values()) - 1.0) < 1e-9, \
    f"Weights must sum to 1.0, got {sum(SCORING_WEIGHTS.values())}"

# ─────────────────────────────────────────────────────────────
# Role-Specific Weight Profiles
# Each profile overrides base weights for signals that matter
# more (or less) for a given role. Non-listed keys use base.
# ─────────────────────────────────────────────────────────────
ROLE_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "backend_engineer": {
        "resume_skill_match":   0.15,
        "resume_experience":    0.10,
        "resume_education":     0.03,
        "github_score":         0.18,
        "competitive_coding":   0.10,
        "portfolio_score":      0.05,
        "linkedin_score":       0.06,
        "stackoverflow_score":  0.06,
        "certification_score":  0.07,
        "research_score":       0.02,
        "live_test_score":      0.13,
        "video_score":          0.03,
        "reference_score":      0.02,
    },
    "data_scientist": {
        "resume_skill_match":   0.14,
        "resume_experience":    0.07,
        "resume_education":     0.08,
        "github_score":         0.12,
        "competitive_coding":   0.08,
        "portfolio_score":      0.06,
        "linkedin_score":       0.06,
        "stackoverflow_score":  0.03,
        "certification_score":  0.08,
        "research_score":       0.12,
        "live_test_score":      0.10,
        "video_score":          0.03,
        "reference_score":      0.03,
    },
    "tech_lead": {
        "resume_skill_match":   0.12,
        "resume_experience":    0.14,
        "resume_education":     0.04,
        "github_score":         0.12,
        "competitive_coding":   0.06,
        "portfolio_score":      0.06,
        "linkedin_score":       0.12,
        "stackoverflow_score":  0.04,
        "certification_score":  0.06,
        "research_score":       0.03,
        "live_test_score":      0.10,
        "video_score":          0.06,
        "reference_score":      0.05,
    },
    "fresher": {
        "resume_skill_match":   0.14,
        "resume_experience":    0.02,
        "resume_education":     0.10,
        "github_score":         0.18,
        "competitive_coding":   0.18,
        "portfolio_score":      0.10,
        "linkedin_score":       0.04,
        "stackoverflow_score":  0.03,
        "certification_score":  0.06,
        "research_score":       0.02,
        "live_test_score":      0.10,
        "video_score":          0.02,
        "reference_score":      0.01,
    },
    "fullstack": {
        "resume_skill_match":   0.15,
        "resume_experience":    0.08,
        "resume_education":     0.04,
        "github_score":         0.16,
        "competitive_coding":   0.08,
        "portfolio_score":      0.14,
        "linkedin_score":       0.06,
        "stackoverflow_score":  0.04,
        "certification_score":  0.06,
        "research_score":       0.02,
        "live_test_score":      0.12,
        "video_score":          0.03,
        "reference_score":      0.02,
    },
    "ml_engineer": {
        "resume_skill_match":   0.14,
        "resume_experience":    0.08,
        "resume_education":     0.07,
        "github_score":         0.15,
        "competitive_coding":   0.08,
        "portfolio_score":      0.06,
        "linkedin_score":       0.05,
        "stackoverflow_score":  0.03,
        "certification_score":  0.08,
        "research_score":       0.10,
        "live_test_score":      0.11,
        "video_score":          0.03,
        "reference_score":      0.02,
    },
}

# Validate all role profiles sum to 1.0
for _role, _weights in ROLE_WEIGHT_PROFILES.items():
    assert abs(sum(_weights.values()) - 1.0) < 1e-9, \
        f"Role '{_role}' weights sum to {sum(_weights.values())}, expected 1.0"

# ─────────────────────────────────────────────────────────────
# Education Scoring
# Maps degree level → base score (0.0–1.0)
# ─────────────────────────────────────────────────────────────
EDUCATION_SCORES: dict[str, float] = {
    "phd":              1.0,
    "doctorate":        1.0,
    "masters":          0.85,
    "master":           0.85,
    "mtech":            0.85,
    "ms":               0.85,
    "msc":              0.80,
    "mba":              0.75,
    "bachelors":        0.65,
    "bachelor":         0.65,
    "btech":            0.65,
    "bs":               0.65,
    "bsc":              0.60,
    "be":               0.65,
    "bca":              0.55,
    "associate":        0.40,
    "diploma":          0.35,
    "high_school":      0.20,
    "self_taught":      0.15,
    "bootcamp":         0.30,
    "unknown":          0.10,
}

# ─────────────────────────────────────────────────────────────
# Experience Thresholds
# Each tuple: (min_years, max_years, label, score_multiplier)
# ─────────────────────────────────────────────────────────────
EXPERIENCE_THRESHOLDS: list[tuple[float, float, str, float]] = [
    (0.0,   0.5,  "no_experience",   0.10),
    (0.5,   1.0,  "intern_level",    0.20),
    (1.0,   2.0,  "junior",          0.35),
    (2.0,   4.0,  "mid_junior",      0.50),
    (4.0,   6.0,  "mid",             0.65),
    (6.0,   8.0,  "mid_senior",      0.75),
    (8.0,  12.0,  "senior",          0.85),
    (12.0, 18.0,  "staff",           0.92),
    (18.0, 25.0,  "principal",       0.97),
    (25.0, 100.0, "distinguished",   1.00),
]

# ─────────────────────────────────────────────────────────────
# Competitive Coding — Rating Percentile Mapping
# Codeforces-style rating → normalized score (0.0–1.0)
# ─────────────────────────────────────────────────────────────
RATING_PERCENTILE: dict[str, dict[str, float]] = {
    "codeforces": {
        "newbie":               0.10,   # < 1200
        "pupil":                0.25,   # 1200–1399
        "specialist":           0.40,   # 1400–1599
        "expert":               0.55,   # 1600–1899
        "candidate_master":     0.70,   # 1900–2099
        "master":               0.82,   # 2100–2299
        "international_master": 0.90,   # 2300–2399
        "grandmaster":          0.95,   # 2400–2599
        "international_grandmaster": 0.98,  # 2600–2999
        "legendary_grandmaster": 1.00,  # 3000+
    },
    "leetcode": {
        "beginner":             0.10,   # < 1400
        "intermediate":         0.30,   # 1400–1599
        "competent":            0.50,   # 1600–1799
        "advanced":             0.65,   # 1800–1999
        "expert":               0.80,   # 2000–2199
        "knight":               0.90,   # 2200–2399
        "guardian":             0.95,   # 2400–2599
        "sage":                 0.98,   # 2600+
    },
    "codechef": {
        "one_star":             0.10,   # < 1400
        "two_star":             0.25,   # 1400–1599
        "three_star":           0.40,   # 1600–1799
        "four_star":            0.55,   # 1800–1999
        "five_star":            0.70,   # 2000–2199
        "six_star":             0.85,   # 2200–2499
        "seven_star":           0.95,   # 2500+
    },
    "hackerrank": {
        "one_star":             0.15,
        "two_star":             0.30,
        "three_star":           0.50,
        "four_star":            0.70,
        "five_star":            0.85,
        "six_star":             0.95,
        "seven_star":           1.00,
    },
}

# ─────────────────────────────────────────────────────────────
# Tier-1 Institution Bonus (additive to education score)
# ─────────────────────────────────────────────────────────────
TIER1_INSTITUTIONS: set[str] = {
    "iit", "nit", "iiit", "bits", "mit", "stanford", "cmu",
    "berkeley", "caltech", "harvard", "oxford", "cambridge",
    "eth zurich", "georgia tech", "princeton", "cornell",
    "university of illinois", "university of washington",
}

TIER1_BONUS: float = 0.08

# ─────────────────────────────────────────────────────────────
# Certification Value Tiers
# ─────────────────────────────────────────────────────────────
CERTIFICATION_TIERS: dict[str, float] = {
    "professional":  1.0,   # AWS Solutions Architect Pro, GCP Pro, etc.
    "associate":     0.65,  # AWS SAA, Azure AZ-104, etc.
    "foundational":  0.35,  # AWS Cloud Practitioner, GCP CDL, etc.
    "speciality":    0.80,  # AWS Security Specialty, etc.
    "vendor_other":  0.50,  # Kubernetes CKA, Terraform, etc.
}


def get_weights_for_role(role: str) -> dict[str, float]:
    """Return scoring weights for a given role, falling back to base weights."""
    return ROLE_WEIGHT_PROFILES.get(role.lower().replace(" ", "_"), SCORING_WEIGHTS)


def get_experience_score(years: float) -> tuple[str, float]:
    """Return (label, score) for the given years of experience."""
    for min_y, max_y, label, score in EXPERIENCE_THRESHOLDS:
        if min_y <= years < max_y:
            return label, score
    return "distinguished", 1.0


def get_education_score(degree: str) -> float:
    """Return normalized score for a degree level."""
    return EDUCATION_SCORES.get(degree.lower().replace(" ", "_"), 0.10)
