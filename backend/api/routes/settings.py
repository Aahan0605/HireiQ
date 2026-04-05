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
