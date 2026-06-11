import os
import logging
import datetime
import json
import uuid
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
import stripe

from db.session import SessionLocal
from db.models import Subscription, StripeWebhookEvent
from api.core.dependencies import get_current_user
from api.core.rbac import require_tenant, Permission, require_permission

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
        # Enforce signing signature validation if secret is set
        if ENDPOINT_SECRET:
            event = stripe.Webhook.construct_event(
                payload, sig_header, ENDPOINT_SECRET
            )
        else:
            # Local fallback / testing mode without signature
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
    
    db = SessionLocal()
    try:
        # Idempotency / Duplicate Check
        existing_event = db.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
        if existing_event:
            logger.info("Stripe Webhook event %s already processed. Skipping.", event_id)
            return {"status": "already_processed"}

        # Record incoming event in audit log
        audit_event = StripeWebhookEvent(
            id=event_id,
            event_type=event_type,
            payload=json.dumps(event),
            status="processing"
        )
        db.add(audit_event)
        db.commit()

        # Handle events
        if event_type == "checkout.session.completed":
            session = event.get("data", {}).get("object", {})
            org_id = session.get("client_reference_id")
            customer_id = session.get("customer")
            sub_id = session.get("subscription")
            plan_name = session.get("metadata", {}).get("plan_name", "Pro")
            
            if org_id:
                sub = db.query(Subscription).filter(Subscription.organization_id == org_id).first()
                if not sub:
                    sub = Subscription(
                        id=str(uuid.uuid4()),
                        organization_id=org_id,
                        plan_name=plan_name,
                        status="active",
                        stripe_customer_id=customer_id,
                        stripe_subscription_id=sub_id
                    )
                    db.add(sub)
                    db.commit()
                    sub = db.query(Subscription).filter(Subscription.organization_id == org_id).first()

                if sub:
                    sub.plan_name = plan_name
                    sub.status = "active"
                    sub.stripe_customer_id = customer_id
                    sub.stripe_subscription_id = sub_id
                    
                    # Fetch subscription details from Stripe if api_key is active
                    if stripe.api_key and sub_id:
                        try:
                            stripe_sub = stripe.Subscription.retrieve(sub_id)
                            period_end = stripe_sub.get("current_period_end")
                            if period_end:
                                sub.current_period_end = datetime.datetime.fromtimestamp(period_end)
                        except Exception as stripe_err:
                            logger.warning("Could not fetch subscription period end: %s", stripe_err)
                    
                    db.commit()
                    logger.info("Subscription upgraded to %s for Org: %s", plan_name, org_id)
                else:
                    logger.error("Subscription record not found and failed to create for Org: %s", org_id)
            else:
                logger.error("Missing client_reference_id (organization_id) in Stripe checkout session")

        elif event_type in ["customer.subscription.created", "customer.subscription.updated"]:
            stripe_sub = event.get("data", {}).get("object", {})
            sub_id = stripe_sub.get("id")
            status_str = stripe_sub.get("status")
            customer_id = stripe_sub.get("customer")
            period_end = stripe_sub.get("current_period_end")
            
            sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
            if not sub and customer_id:
                sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()

            if sub:
                sub.status = status_str
                if period_end:
                    sub.current_period_end = datetime.datetime.fromtimestamp(period_end)
                
                # Determine plan name from Stripe subscription items price ID
                items = stripe_sub.get("items", {}).get("data", [])
                if items:
                    price_id = items[0].get("price", {}).get("id")
                    price_pro = os.getenv("STRIPE_PRICE_PRO") or os.getenv("STRIPE_PRICE_PRO_ID", "price_1MockProPriceID")
                    price_biz = os.getenv("STRIPE_PRICE_BUSINESS") or os.getenv("STRIPE_PRICE_BUSINESS_ID", "price_1MockBusinessPriceID")
                    price_ent = os.getenv("STRIPE_PRICE_ENTERPRISE") or os.getenv("STRIPE_PRICE_ENTERPRISE_ID", "price_1MockEnterprisePriceID")
                    
                    if price_id == price_pro:
                        sub.plan_name = "Pro"
                    elif price_id == price_biz:
                        sub.plan_name = "Business"
                    elif price_id == price_ent:
                        sub.plan_name = "Enterprise"
                    else:
                        sub.plan_name = stripe_sub.get("metadata", {}).get("plan_name", sub.plan_name)

                # Handle downgrades on cancellations
                if status_str in ["canceled", "unpaid", "incomplete_expired"]:
                    sub.plan_name = "Free"
                    
                db.commit()
                logger.info("Subscription %s updated to status %s and plan %s", sub_id, status_str, sub.plan_name)

        elif event_type == "customer.subscription.deleted":
            stripe_sub = event.get("data", {}).get("object", {})
            sub_id = stripe_sub.get("id")
            
            sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
            if sub:
                sub.plan_name = "Free"
                sub.status = "canceled"
                db.commit()
                logger.info("Subscription %s deleted (downgraded to Free)", sub_id)

        elif event_type == "invoice.payment_succeeded":
            invoice = event.get("data", {}).get("object", {})
            sub_id = invoice.get("subscription")
            
            if sub_id:
                sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
                if sub:
                    sub.status = "active"
                    # Reset usage counters on successful payment cycle renewal
                    sub.cv_parses_used = 0
                    sub.jobs_created_used = 0
                    db.commit()
                    logger.info("Payment succeeded for subscription %s. Usage counters reset.", sub_id)

        elif event_type == "invoice.payment_failed":
            invoice = event.get("data", {}).get("object", {})
            sub_id = invoice.get("subscription")
            
            if sub_id:
                sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == sub_id).first()
                if sub:
                    sub.status = "past_due"
                    db.commit()
                    logger.warning("Payment failed for subscription %s. Marked as past_due.", sub_id)

        # Mark audit event as processed successfully
        audit_event.status = "processed"
        db.commit()

    except Exception as e:
        db.rollback()
        logger.error("Error processing Stripe Webhook event: %s", e)
        # Attempt to mark the audit event as failed
        try:
            fail_event = db.query(StripeWebhookEvent).filter(StripeWebhookEvent.id == event_id).first()
            if fail_event:
                fail_event.status = "failed"
                fail_event.error_message = str(e)
                db.commit()
        except Exception as audit_err:
            logger.error("Failed to write webhook audit failure: %s", audit_err)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error handling webhook"
        )
    finally:
        db.close()

    return {"status": "success"}


@router.get("/audit-logs", dependencies=[Depends(require_tenant)])
def get_webhook_audit_logs(db: Session = Depends(SessionLocal)):
    """Retrieve lists of received Stripe webhook events for SaaS administration monitoring."""
    events = db.query(StripeWebhookEvent).order_by(StripeWebhookEvent.processed_at.desc()).limit(100).all()
    return [{
        "id": e.id,
        "event_type": e.event_type,
        "processed_at": e.processed_at.isoformat(),
        "status": e.status,
        "error_message": e.error_message
    } for e in events]


@router.post("/create-checkout-session", dependencies=[Depends(require_permission(Permission.MANAGE_BILLING))])
async def create_checkout_session(
    plan_name: str,
    tenant_id: str = Depends(require_tenant),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a Stripe Checkout session mapping the plan_name to configured price IDs,
    associating with organization tenant ID and existing Stripe customer if available.
    """
    if not stripe.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe API is not configured on this server."
        )
        
    price_id = (
        os.getenv(f"STRIPE_PRICE_{plan_name.upper()}")
        or os.getenv(f"STRIPE_PRICE_{plan_name.upper()}_ID")
    )
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan name or price not configured for {plan_name}"
        )
        
    db = SessionLocal()
    stripe_customer_id = None
    try:
        sub = db.query(Subscription).filter(Subscription.organization_id == tenant_id).first()
        if sub:
            stripe_customer_id = sub.stripe_customer_id
    finally:
        db.close()
        
    # Build checkout parameters
    checkout_params = {
        "payment_method_types": ["card"],
        "line_items": [{
            "price": price_id,
            "quantity": 1
        }],
        "mode": "subscription",
        "client_reference_id": tenant_id,
        "metadata": {
            "plan_name": plan_name,
            "organization_id": tenant_id
        },
        "success_url": os.getenv("FRONTEND_URL", "http://localhost:5173") + "/settings?tab=billing&checkout=success",
        "cancel_url": os.getenv("FRONTEND_URL", "http://localhost:5173") + "/settings?tab=billing&checkout=cancel"
    }
    
    if stripe_customer_id:
        checkout_params["customer"] = stripe_customer_id
    else:
        # Fallback to current user's email if not a Stripe customer yet
        checkout_params["customer_email"] = current_user.get("email")
        
    try:
        session = stripe.checkout.Session.create(**checkout_params)
        return {"url": session.url, "checkout_url": session.url}
    except Exception as e:
        logger.error("Failed to create Stripe Checkout session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe Checkout error: {str(e)}"
        )
