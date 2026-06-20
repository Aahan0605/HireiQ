import pytest
import uuid
import httpx
from api.main import app
from conftest import MOCK_DB
import api.routes.billing

@pytest.fixture(autouse=True)
def reset_endpoint_secret():
    api.routes.billing.ENDPOINT_SECRET = None

def create_mock_recruiter(email="billing_test@example.com", plan="free"):
    org_id = str(uuid.uuid4())
    recruiter = {
        "id": org_id,
        "email": email,
        "hashed_password": "pwd",  # pragma: allowlist secret
        "role": "Owner",
        "company": "Billing Corp",
        "is_verified": True,
        "plan": plan
    }
    MOCK_DB["recruiters"].append(recruiter)
    return org_id, recruiter

@pytest.mark.asyncio
async def test_webhook_checkout_session_completed():
    org_id, rec = create_mock_recruiter()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        checkout_payload = {
            "id": f"evt_{uuid.uuid4().hex[:8]}",
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
        res = await ac.post("/api/v1/billing/webhook", json=checkout_payload)
        assert res.status_code == 200
        assert rec["plan"] == "pro"

@pytest.mark.asyncio
async def test_webhook_customer_subscription_deleted():
    org_id, rec = create_mock_recruiter(plan="pro")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        deleted_payload = {
            "id": f"evt_{uuid.uuid4().hex[:8]}",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "metadata": {
                        "organization_id": org_id
                    }
                }
            }
        }
        res = await ac.post("/api/v1/billing/webhook", json=deleted_payload)
        assert res.status_code == 200
        assert rec["plan"] == "free"

@pytest.mark.asyncio
async def test_webhook_invoice_payment_failed_grace_period():
    org_id, rec = create_mock_recruiter(plan="pro")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        failed_payload = {
            "id": f"evt_{uuid.uuid4().hex[:8]}",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "metadata": {
                        "organization_id": org_id
                    }
                }
            }
        }
        res = await ac.post("/api/v1/billing/webhook", json=failed_payload)
        assert res.status_code == 200
        assert rec["plan"] == "pro"  # plan unchanged

@pytest.mark.asyncio
async def test_webhook_malformed_payload():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/billing/webhook", content="invalid json")
        assert res.status_code == 400

@pytest.mark.asyncio
async def test_webhook_missing_event_id():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        missing_id_payload = {
            "type": "checkout.session.completed"
        }
        res = await ac.post("/api/v1/billing/webhook", json=missing_id_payload)
        assert res.status_code == 400
