"""HireIQ Signals — External signal fetchers and scorers."""

from signals.github_signal import fetch_github_signals, score_github
from signals.coding_signal import (
    fetch_codeforces, fetch_codechef, fetch_leetcode,
    score_competitive_coding,
)
from signals.linkedin_signal import (
    extract_linkedin_signals_from_resume, score_linkedin,
    extract_linkedin_url,
)
from signals.cert_verifier import (
    detect_certifications, verify_cert, score_certifications,
)
from signals.portfolio_crawler import crawl_portfolio, score_portfolio

__all__ = [
    "fetch_github_signals", "score_github",
    "fetch_codeforces", "fetch_codechef", "fetch_leetcode",
    "score_competitive_coding",
    "extract_linkedin_signals_from_resume", "score_linkedin",
    "extract_linkedin_url",
    "detect_certifications", "verify_cert", "score_certifications",
    "crawl_portfolio", "score_portfolio",
]
