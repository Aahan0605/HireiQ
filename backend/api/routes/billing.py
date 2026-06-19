import os
import logging
from datetime import datetime
import json
from fastapi import APIRouter, Request, HTTPException, status, Depends, Body
from db.session import SessionLocal
from db.models import Subscription
import stripe

from api.core.dependencies import get_current_user
from api.core.rbac import require_tenant, Permission, require_permission
from db import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)

# Load Stripe secrets
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
ENDPOINT_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Robust Stripe webhook endpoint managing subscription state with idempotency protection.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if ENDPOINT_SECRET and not sig_header:
        logger.error("Missing stripe-signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
        
    try:
        if ENDPOINT_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, ENDPOINT_SECRET
            )
        else:
            event = json.loads(payload.decode("utf-8"))
    except ValueError as e:
        logger.error("Invalid Stripe payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error("Stripe signature verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    event_id = event.get("id")
    event_type = event.get("type")
    
    if not event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event ID"
        )

    logger.info("Processing Stripe Webhook Event: %s (ID: %s)", event_type, event_id)
    
    supabase = get_supabase()
    
    try:
        # Idempotency check
        res = supabase.table("stripe_webhook_events").select("*").eq("id", event_id).execute()
        if res.data:
            logger.info("Stripe Webhook event %s already processed. Skipping.", event_id)
            return {"status": "already_processed"}

        # Record incoming event
        supabase.table("stripe_webhook_events").insert({
            "id": event_id,
            "event_type": event_type,
            "status": "processing"
        }).execute()

        # Handle events
        if event_type == "checkout.session.completed":
            session = event.get("data", {}).get("object", {})
            org_id = session.get("client_reference_id")
            plan_name = session.get("metadata", {}).get("plan_name", "Pro")
            
            if org_id:
                # Update recruiter plan
                supabase.table("recruiters").update({
                    "plan": plan_name.lower()
                }).eq("id", org_id).execute()
                logger.info("Subscription upgraded to %s for Org: %s", plan_name, org_id)
            else:
                logger.error("Missing client_reference_id (organization_id) in Stripe checkout session")

        elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
            stripe_sub = event.get("data", {}).get("object", {})
            status_str = stripe_sub.get("status")
            org_id = stripe_sub.get("metadata", {}).get("organization_id")
            
            if org_id:
                plan_name = "free"
                
                # Determine plan name from Stripe subscription items price ID
                items = stripe_sub.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id")
                    price_pro = os.getenv("STRIPE_PRICE_PRO") or os.getenv("STRIPE_PRICE_PRO_ID", "price_1MockProPriceID")
                    price_biz = os.getenv("STRIPE_PRICE_BUSINESS") or os.getenv("STRIPE_PRICE_BUSINESS_ID", "price_1MockBusinessPriceID")
                    price_ent = os.getenv("STRIPE_PRICE_ENTERPRISE") or os.getenv("STRIPE_PRICE_ENTERPRISE_ID", "price_1MockEnterprisePriceID")
                    
                    if price_id == price_pro:
                        plan_name = "pro"
                    elif price_id == price_biz:
                        plan_name = "pro"  # fallback or map to pro/enterprise
                    elif price_id == price_ent:
                        plan_name = "enterprise"
                    else:
                        plan_name = stripe_sub.get("metadata", {}).get("plan_name", "pro").lower()

                # Handle downgrades on cancellations
                if status_str in ["canceled", "unpaid", "incomplete_expired"]:
                    plan_name = "free"
                    
                supabase.table("recruiters").update({
                    "plan": plan_name
                }).eq("id", org_id).execute()
                logger.info("Subscription updated to status %s and plan %s for Org %s", status_str, plan_name, org_id)

        elif event_type == "customer.subscription.deleted":
            stripe_sub = event.get("data", {}).get("object", {})
            org_id = stripe_sub.get("metadata", {}).get("organization_id")
            
            if org_id:
                supabase.table("recruiters").update({
                    "plan": "free"
                }).eq("id", org_id).execute()
                logger.info("Subscription deleted (downgraded to Free) for Org %s", org_id)

        elif event_type == "invoice.payment_succeeded":
            invoice = event.get("data", {}).get("object", {})
            sub_id = invoice.get("subscription")
            
            if sub_id and stripe.api_key:
                try:
                    # Retrieve subscription to get org_id
                    stripe_sub = stripe.Subscription.retrieve(sub_id)
                    org_id = stripe_sub.get("metadata", {}).get("organization_id")
                    if org_id:
                        # Reset monthly CV upload counter
                        supabase.table("recruiters").update({
                            "cv_upload_count": 0
                        }).eq("id", org_id).execute()
                        logger.info("Payment succeeded for subscription %s. Reset CV upload count for Org %s.", sub_id, org_id)
                except Exception as stripe_err:
                    logger.warning("Could not retrieve subscription details during invoice success: %s", stripe_err)

        # Mark event as processed successfully
        supabase.table("stripe_webhook_events").update({
            "status": "processed"
        }).eq("id", event_id).execute()

    except Exception as e:
        logger.error("Error processing Stripe Webhook event: %s", e)
        try:
            supabase.table("stripe_webhook_events").update({
                "status": "failed",
                "error_message": str(e)
            }).eq("id", event_id).execute()
        except Exception as audit_err:
            logger.error("Failed to write webhook audit failure: %s", audit_err)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error handling webhook"
        )

    return {"status": "success"}

@router.get("/audit-logs", dependencies=[Depends(require_tenant)])
async def get_webhook_audit_logs():
    """Retrieve lists of received Stripe webhook events for SaaS administration monitoring."""
    supabase = get_supabase()
    res = supabase.table("stripe_webhook_events").select("*").order("processed_at", desc=True).limit(100).execute()
    return [{
        "id": e["id"],
        "event_type": e["event_type"],
        "processed_at": e["processed_at"],
        "status": e["status"],
        "error_message": e["error_message"]
    } for e in res.data]

@router.post("/create-checkout-session")
async def create_checkout_session(
    plan_name: str = Body(..., embed=True),
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user)
):
    price_map = {
        "Pro": os.getenv("STRIPE_PRICE_PRO_ID", ""),
        "Business": os.getenv("STRIPE_PRICE_BUSINESS_ID", ""),
        "Enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE_ID", ""),
    }
    price_id = price_map.get(plan_name)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"No Stripe price configured for plan: {plan_name}")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    db = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.organization_id == tenant_id).first()
        customer_id = sub.stripe_customer_id if sub and sub.stripe_customer_id else None

        params = {
            "payment_method_types": ["card"],
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": f"{frontend_url}/settings?tab=billing&checkout=success",
            "cancel_url": f"{frontend_url}/settings?tab=billing&checkout=cancelled",
            "metadata": {"tenant_id": tenant_id, "plan_name": plan_name},
            "client_reference_id": tenant_id,
        }
        if customer_id:
            params["customer"] = customer_id
        else:
            params["customer_email"] = current_user.get("email", "")

        session = stripe.checkout.Session.create(**params)
        return {"checkout_url": session.url}
    finally:
        db.close()
