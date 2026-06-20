import pytest
import uuid
import httpx
from unittest.mock import patch
import stripe
from api.main import app
from conftest import MOCK_DB
import os

@pytest.mark.asyncio
async def test_billing_webhook():
    # 1. Setup a test organization (recruiter)
    org_id = str(uuid.uuid4())
    recruiter_record = {
        "id": org_id,
        "email": "billing_test@example.com",
        "hashed_password": "hashed_pwd",  # pragma: allowlist secret
        "role": "Owner",
        "company": "Billing Corp",
        "is_verified": True,
        "plan": "free"
    }
    MOCK_DB["recruiters"].append(recruiter_record)

    # Configure mock webhook secret on the billing route module
    import api.routes.billing
    api.routes.billing.ENDPOINT_SECRET = "whsec_testsecret"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Test 1: Test that sending a request to /billing/webhook with an invalid signature header or missing signature returns 400.
        res = await ac.post("/api/v1/billing/webhook", content=b"{}")
        assert res.status_code == 400
        assert "Missing stripe-signature header" in res.json()["detail"]

        # Invalid signature (mock construct_event raising SignatureVerificationError)
        def mock_construct_event_fail(payload, sig, secret):
            raise stripe.error.SignatureVerificationError("Invalid signature", sig)
            
        with patch("stripe.Webhook.construct_event", side_effect=mock_construct_event_fail):
            res = await ac.post(
                "/api/v1/billing/webhook",
                content=b"{}",
                headers={"stripe-signature": "invalid_sig"}
            )
            assert res.status_code == 400
            assert "Invalid signature" in res.json()["detail"]

        # Test 2: Test that sending a valid Stripe checkout.session.completed event updates the recruiter's plan correctly.
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        mock_event = {
            "id": event_id,
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "client_reference_id": org_id,
                    "metadata": {
                        "plan_name": "Pro"
                    }
                }
            }
        }
        
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            res = await ac.post(
                "/api/v1/billing/webhook",
                content=b"{}",
                headers={"stripe-signature": "valid_sig"}
            )
            assert res.status_code == 200
            assert res.json()["status"] == "success"
            
            # Verify recruiter's plan was upgraded to pro
            recruiter = next(r for r in MOCK_DB["recruiters"] if r["id"] == org_id)
            assert recruiter["plan"] == "pro"

        # Test 3: Test replay protection: sending the same Stripe event ID twice returns a 200/skip response (already_processed).
        with patch("stripe.Webhook.construct_event", return_value=mock_event):
            res2 = await ac.post(
                "/api/v1/billing/webhook",
                content=b"{}",
                headers={"stripe-signature": "valid_sig"}
            )
            assert res2.status_code == 200
            assert res2.json()["status"] == "already_processed"
