"""
Hybrid Database Layer — Supabase (primary) + SQLite (fallback).

When SUPABASE_URL and SUPABASE_KEY are set and reachable, all data flows
through Supabase.  If the connection fails (timeout, paused project, bad
credentials), the system transparently falls back to a local SQLite
database so the app always works.

Schema (applied automatically to SQLite; run the SQL block in your
Supabase SQL editor for the remote variant):

    create table if not exists candidates (
        id          text primary key,
        name        text,
        role        text,
        email       text,
        github      text,
        linkedin    text,
        location    text,
        score       integer default 0,
        status      text default 'Match',
        summary     text,
        skills      text,          -- JSON array
        experience  text,          -- JSON array
        job_matches text,          -- JSON array
        radar_data  text,          -- JSON array
        analyzed_at text default (datetime('now'))
    );

    create table if not exists jobs (
        id          text primary key,
        title       text,
        company     text,
        location    text,
        description text,
        required_skills text,
        preferred_skills text,
        experience_required integer default 0,
        max_experience integer default 99,
        salary_range text,
        status      text default 'active',
        created_at  text default (datetime('now'))
    );

    create table if not exists analytics (
        id          integer primary key autoincrement,
        event_type  text,
        payload     text,
        created_at  text default (datetime('now'))
    );
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ─── Supabase Client (optional) ────────────────────────────────

_supabase_client = None
_supabase_available: bool | None = None  # None = not yet tested


def _try_init_supabase():
    """Attempt to create a Supabase client. Return None on failure."""
    global _supabase_client, _supabase_available
    if _supabase_available is False:
        return None
    if _supabase_client is not None:
        return _supabase_client

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        _supabase_available = False
        logger.info("Supabase credentials not set — using SQLite fallback.")
        return None

    try:
        from supabase import create_client
        import concurrent.futures
        client = create_client(url, key)

        # Quick connectivity check with a 5-second timeout to avoid
        # blocking when the Supabase project is paused / unreachable.
        def _ping():
            client.table("candidates").select("id").limit(1).execute()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_ping).result(timeout=5)

        _supabase_client = client
        _supabase_available = True
        logger.info("✓ Connected to Supabase at %s", url)
        return client
    except Exception as e:
        _supabase_available = False
        logger.warning("Supabase unavailable (%s) — using SQLite fallback.", e)
        return None


# ─── SQLite Client (always available) ──────────────────────────

_DB_PATH = Path(__file__).resolve().parent / "hireiq.db"
_local = threading.local()


def _get_sqlite() -> sqlite3.Connection:
    """Return a thread-local SQLite connection, creating tables on first use."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        _bootstrap_sqlite(conn)
        _local.conn = conn
    return conn


def _bootstrap_sqlite(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS candidates (
            id          TEXT PRIMARY KEY,
            name        TEXT,
            role        TEXT,
            email       TEXT,
            github      TEXT,
            linkedin    TEXT,
            location    TEXT,
            score       INTEGER DEFAULT 0,
            status      TEXT DEFAULT 'Match',
            summary     TEXT,
            skills      TEXT,
            experience  TEXT,
            job_matches TEXT,
            radar_data  TEXT,
            analyzed_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id          TEXT PRIMARY KEY,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            description TEXT,
            required_skills TEXT,
            preferred_skills TEXT,
            experience_required INTEGER DEFAULT 0,
            max_experience INTEGER DEFAULT 99,
            salary_range TEXT,
            status      TEXT DEFAULT 'active',
            created_at  TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS analytics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT,
            payload     TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );
    """)


# ─── Helper Serializers ────────────────────────────────────────

def _json_dumps(v: Any) -> str:
    return json.dumps(v) if v else "[]"

def _json_loads(v: str | None) -> Any:
    if v is None:
        return []
    try:
        return json.loads(v)
    except Exception:
        return []


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert an sqlite3.Row to a regular dict, deserializing JSON columns."""
    d = dict(row)
    for col in ("skills", "experience", "job_matches", "radar_data"):
        if col in d:
            d[col] = _json_loads(d[col])
    return d


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — candidates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def save_candidate(candidate: dict) -> dict:
    """Upsert a candidate. Tries Supabase first, then SQLite."""
    sb = _try_init_supabase()
    if sb:
        try:
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
                "job_matches": candidate.get("jobMatches", candidate.get("job_matches", [])),
                "radar_data":  candidate.get("radarData", candidate.get("radar_data", [])),
            }
            result = sb.table("candidates").upsert(row).execute()
            return result.data[0] if result.data else row
        except Exception as e:
            logger.warning("Supabase upsert failed (%s) — falling back to SQLite", e)

    # SQLite fallback
    conn = _get_sqlite()
    conn.execute("""
        INSERT OR REPLACE INTO candidates
            (id, name, role, email, github, linkedin, location, score, status,
             summary, skills, experience, job_matches, radar_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        candidate.get("id"),
        candidate.get("name"),
        candidate.get("role"),
        candidate.get("email"),
        candidate.get("github"),
        candidate.get("linkedin"),
        candidate.get("location", "Remote"),
        candidate.get("score", 0),
        candidate.get("status", "Match"),
        candidate.get("summary", ""),
        _json_dumps(candidate.get("skills", [])),
        _json_dumps(candidate.get("experience", [])),
        _json_dumps(candidate.get("jobMatches", candidate.get("job_matches", []))),
        _json_dumps(candidate.get("radarData", candidate.get("radar_data", []))),
    ))
    conn.commit()
    return candidate


async def fetch_all_candidates() -> list[dict]:
    """Fetch all candidates ordered by score descending."""
    sb = _try_init_supabase()
    if sb:
        try:
            result = sb.table("candidates").select("*").order("score", desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.warning("Supabase fetch failed (%s) — falling back to SQLite", e)

    conn = _get_sqlite()
    rows = conn.execute("SELECT * FROM candidates ORDER BY score DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


async def fetch_candidate_by_id(candidate_id: str) -> dict | None:
    sb = _try_init_supabase()
    if sb:
        try:
            result = sb.table("candidates").select("*").eq("id", candidate_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning("Supabase fetch-by-id failed (%s) — falling back to SQLite", e)

    conn = _get_sqlite()
    row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    return _row_to_dict(row) if row else None


async def delete_candidate(candidate_id: str) -> bool:
    sb = _try_init_supabase()
    if sb:
        try:
            sb.table("candidates").delete().eq("id", candidate_id).execute()
            # Also delete from SQLite mirror
        except Exception as e:
            logger.warning("Supabase delete failed: %s", e)

    conn = _get_sqlite()
    conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
    conn.commit()
    return True


async def get_candidate_count() -> int:
    sb = _try_init_supabase()
    if sb:
        try:
            result = sb.table("candidates").select("id", count="exact").execute()
            return result.count or 0
        except Exception:
            pass
    conn = _get_sqlite()
    row = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()
    return row[0] if row else 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PUBLIC API — analytics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def log_analytics_event(event_type: str, payload: dict):
    conn = _get_sqlite()
    conn.execute(
        "INSERT INTO analytics (event_type, payload) VALUES (?, ?)",
        (event_type, _json_dumps(payload)),
    )
    conn.commit()


async def get_analytics_summary() -> dict:
    conn = _get_sqlite()
    total = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    strong = conn.execute("SELECT COUNT(*) FROM candidates WHERE score >= 85").fetchone()[0]
    match = conn.execute("SELECT COUNT(*) FROM candidates WHERE score >= 60 AND score < 85").fetchone()[0]
    weak = conn.execute("SELECT COUNT(*) FROM candidates WHERE score < 60").fetchone()[0]
    avg_score = conn.execute("SELECT COALESCE(AVG(score), 0) FROM candidates").fetchone()[0]

    # Recent uploads (last 7 days)
    recent = conn.execute("""
        SELECT COUNT(*) FROM candidates
        WHERE analyzed_at >= datetime('now', '-7 days')
    """).fetchone()[0]

    # Top skills across all candidates
    rows = conn.execute("SELECT skills FROM candidates").fetchall()
    skill_freq: dict[str, int] = {}
    for r in rows:
        for s in _json_loads(r[0]):
            skill_freq[s] = skill_freq.get(s, 0) + 1

    top_skills = sorted(skill_freq.items(), key=lambda x: -x[1])[:10]

    return {
        "total_candidates": total,
        "strong_matches": strong,
        "matches": match,
        "weak_matches": weak,
        "average_score": round(avg_score, 1),
        "recent_uploads_7d": recent,
        "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
        "storage_backend": "supabase" if _supabase_available else "sqlite",
    }


def get_db_status() -> dict:
    """Return connection status info for the Settings page."""
    return {
        "supabase_available": _supabase_available or False,
        "supabase_url": os.environ.get("SUPABASE_URL", ""),
        "sqlite_path": str(_DB_PATH),
        "sqlite_size_mb": round(_DB_PATH.stat().st_size / 1024 / 1024, 2) if _DB_PATH.exists() else 0,
    }
