"""
Supabase client — single shared instance for all DB operations.

Run this SQL once in your Supabase SQL editor to create the table:

    create table candidates (
        id          text primary key,
        name        text,
        role        text,
        email       text,
        github      text,
        linkedin    text,
        location    text,
        score       integer,
        status      text,
        summary     text,
        skills      jsonb,
        experience  jsonb,
        job_matches jsonb,
        radar_data  jsonb,
        analyzed_at timestamptz default now()
    );
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        _client = create_client(url, key)
    return _client


async def save_candidate(candidate: dict) -> dict:
    """Upsert a candidate row. Returns the saved row."""
    db = get_client()
    row = {
        "id":          candidate.get("id"),
        "name":        candidate.get("name"),
        "role":        candidate.get("role"),
        "email":       candidate.get("email"),
        "github":      candidate.get("github"),
        "linkedin":    candidate.get("linkedin"),
        "location":    candidate.get("location", "Remote"),
        "score":       candidate.get("score", 0),
        "status":      candidate.get("status", "Match"),
        "summary":     candidate.get("summary", ""),
        "skills":      candidate.get("skills", []),
        "experience":  candidate.get("experience", []),
        "job_matches": candidate.get("jobMatches", []),
        "radar_data":  candidate.get("radarData", []),
    }
    result = db.table("candidates").upsert(row).execute()
    return result.data[0] if result.data else row


async def fetch_all_candidates() -> list[dict]:
    """Fetch all candidates ordered by score descending."""
    db = get_client()
    result = db.table("candidates").select("*").order("score", desc=True).execute()
    return result.data or []


async def fetch_candidate_by_id(candidate_id: str) -> dict | None:
    db = get_client()
    result = db.table("candidates").select("*").eq("id", candidate_id).execute()
    return result.data[0] if result.data else None
