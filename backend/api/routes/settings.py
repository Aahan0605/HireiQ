from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.core.dependencies import get_current_user
from api.core.rbac import require_tenant

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
    dependencies=[Depends(require_tenant)]
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
    """Return analytics summary from database."""
    from db.supabase_client import get_analytics_summary
    try:
        db_analytics = await get_analytics_summary()
        return db_analytics
    except Exception as e:
        return {
            "total_candidates": 0,
            "strong_matches": 0,
            "matches": 0,
            "weak_matches": 0,
            "average_score": 0.0,
            "recent_uploads_7d": 0,
            "top_skills": [],
            "storage_backend": "sqlite",
            "sqlite_size_mb": 0.0
        }


@router.get("/worker-status")
def get_worker_status():
    """Check if the Redis broker and Celery worker are online."""
    from tasks.worker import celery_app
    try:
        # Check active workers
        ping_result = celery_app.control.ping(timeout=0.3)
        if ping_result:
            return {"status": "online", "message": f"Active worker(s) detected: {list(ping_result[0].keys()) if ping_result else ''}"}
        else:
            return {"status": "fallback", "message": "Redis online, worker process offline. Using local background tasks fallback."}
    except Exception:
        return {"status": "fallback", "message": "Redis broker offline. Using local background tasks fallback."}


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
def create_checkout_session(req: CheckoutSessionRequest, tenant_id: str = Depends(require_tenant)):
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
        "Business": os.getenv("STRIPE_PRICE_BUSINESS_ID", "price_1MockBusinessPriceID"),
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
            client_reference_id=tenant_id,
            metadata={"plan_name": req.plan_name},
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdatePlanRequest(BaseModel):
    plan_name: str


@router.post("/billing/update-plan")
def update_plan(req: UpdatePlanRequest, tenant_id: str = Depends(require_tenant)):
    """Manually update the plan for testing/mock purposes."""
    from db.session import SessionLocal
    from db.models import Subscription
    from fastapi import HTTPException
    db = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.organization_id == tenant_id).first()
        if sub:
            sub.plan_name = req.plan_name
            sub.status = "active"
            db.commit()
            return {"status": "success", "plan_name": sub.plan_name}
        else:
            raise HTTPException(status_code=404, detail="Subscription record not found")
    finally:
        db.close()


