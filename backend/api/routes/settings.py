from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["Settings"])


class Weights(BaseModel):
    resume: float = 0.4
    github: float = 0.3
    leetcode: float = 0.2
    portfolio: float = 0.1


class Thresholds(BaseModel):
    strong: int = 85
    match: int = 60
    weak: int = 40


# ── Shared in-memory store ─────────────────────────────────────
# Other routes import `active_weights` to apply user-configured weights.
# Time Complexity: O(1) reads/writes
active_weights: dict[str, float] = {
    "resume":    0.4,
    "github":    0.3,
    "leetcode":  0.2,
    "portfolio": 0.1,
}

active_thresholds: dict[str, int] = {
    "strong": 85,
    "match":  60,
    "weak":   40,
}


@router.post("/weights")
def update_weights(weights: Weights):
    # Time Complexity: O(1)
    global active_weights
    active_weights = weights.model_dump()
    return {"status": "saved", "weights": active_weights}


@router.post("/thresholds")
def update_thresholds(thresholds: Thresholds):
    # Time Complexity: O(1)
    global active_thresholds
    active_thresholds = thresholds.model_dump()
    return {"status": "saved", "thresholds": active_thresholds}


@router.get("/weights")
def get_weights():
    # Time Complexity: O(1)
    return active_weights


@router.get("/thresholds")
def get_thresholds():
    # Time Complexity: O(1)
    return active_thresholds


@router.get("/analytics")
async def get_analytics():
    """Return analytics summary from database + in-memory seeded data."""
    from db.supabase_client import get_analytics_summary
    from api.routes.candidates import candidates_db

    db_analytics = await get_analytics_summary()

    # Merge seeded in-memory candidates into the analytics when DB is sparse
    seeded_count = len(candidates_db)
    if seeded_count > 0:
        seeded_strong = sum(1 for c in candidates_db if c.get("score", 0) >= 85)
        seeded_match  = sum(1 for c in candidates_db if 60 <= c.get("score", 0) < 85)
        seeded_avg    = sum(c.get("score", 0) for c in candidates_db) / seeded_count

        db_total = db_analytics.get("total_candidates", 0)
        combined_total = db_total + seeded_count
        combined_strong = db_analytics.get("strong_matches", 0) + seeded_strong
        combined_match  = db_analytics.get("matches", 0) + seeded_match

        # Weighted average score
        db_avg = db_analytics.get("average_score", 0)
        combined_avg = ((db_avg * db_total) + (seeded_avg * seeded_count)) / combined_total if combined_total > 0 else 0

        db_analytics["total_candidates"] = combined_total
        db_analytics["strong_matches"]   = combined_strong
        db_analytics["matches"]          = combined_match
        db_analytics["average_score"]    = round(combined_avg, 1)

    return db_analytics


@router.get("/db-status")
def get_db_status():
    """Return database connection status."""
    from db.supabase_client import get_db_status as _status
    return _status()
