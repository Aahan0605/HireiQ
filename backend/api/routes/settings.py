from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.core.dependencies import get_current_user

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(get_current_user)]
)


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


class CheckoutSessionRequest(BaseModel):
    plan_name: str
    success_url: str
    cancel_url: str


@router.post("/billing/create-checkout-session")
def create_checkout_session(req: CheckoutSessionRequest):
    """Create a Stripe Checkout session for subscription plans."""
    import stripe
    import os
    from fastapi import HTTPException
    
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    if not stripe.api_key:
        # Graceful fallback: return a mock success URL to simulate checkout completion
        return {"url": f"{req.success_url}?session_id=mock_session_{os.urandom(8).hex()}"}
        
    price_map = {
        "Pro": os.getenv("STRIPE_PRICE_PRO_ID", "price_1MockProPriceID"),
        "Enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE_ID", "price_1MockEnterprisePriceID")
    }
    
    price_id = price_map.get(req.plan_name)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
        
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

