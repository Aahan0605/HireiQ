import pytest
import uuid
import httpx
from api.main import app
from conftest import MOCK_DB

async def register_and_login(ac, email, role, company):
    password = "Password123!"  # pragma: allowlist secret
    reg_res = await ac.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "role": role,
        "company": company,
        "full_name": f"{role} User"
    })
    assert reg_res.status_code == 201
    user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
    user_record["is_verified"] = True
    
    login_res = await ac.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_record["id"]

@pytest.mark.asyncio
async def test_gdpr_export_success():
    email = f"a_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, tenant_id = await register_and_login(ac, email, "Owner", "Corp A")
        
        candidate_id = str(uuid.uuid4())
        MOCK_DB["candidates"].append({
            "id": candidate_id,
            "full_name": "GDPR John Doe",
            "email": "john.doe@example.com",
            "role": "Software Engineer",
            "status": "Screening",
            "recruiter_id": tenant_id
        })

        res = await ac.get(f"/api/v1/candidates/{candidate_id}/gdpr-export", headers=headers)
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        assert res.json()["exported_data"]["name"] == "GDPR John Doe"

@pytest.mark.asyncio
async def test_gdpr_export_isolation():
    email_a = f"a_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"b_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers_a, tenant_a_id = await register_and_login(ac, email_a, "Owner", "Corp A")
        headers_b, _ = await register_and_login(ac, email_b, "Owner", "Corp B")
        
        candidate_id = str(uuid.uuid4())
        MOCK_DB["candidates"].append({
            "id": candidate_id,
            "full_name": "GDPR John Doe",
            "email": "john.doe@example.com",
            "role": "Software Engineer",
            "status": "Screening",
            "recruiter_id": tenant_a_id
        })

        res = await ac.get(f"/api/v1/candidates/{candidate_id}/gdpr-export", headers=headers_b)
        assert res.status_code in [403, 404]

@pytest.mark.asyncio
async def test_gdpr_forget_success():
    email = f"a_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, tenant_id = await register_and_login(ac, email, "Owner", "Corp A")
        
        candidate_id = str(uuid.uuid4())
        MOCK_DB["candidates"].append({
            "id": candidate_id,
            "full_name": "GDPR John Doe",
            "email": "john.doe@example.com",
            "role": "Software Engineer",
            "status": "Screening",
            "recruiter_id": tenant_id
        })

        res = await ac.delete(f"/api/v1/candidates/{candidate_id}/gdpr-forget", headers=headers)
        assert res.status_code == 200
        assert "successfully forgotten" in res.json()["message"]

        # Subsequent export returns 404
        res_export = await ac.get(f"/api/v1/candidates/{candidate_id}/gdpr-export", headers=headers)
        assert res_export.status_code == 404

@pytest.mark.asyncio
async def test_gdpr_forget_isolation():
    email_a = f"a_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"b_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers_a, tenant_a_id = await register_and_login(ac, email_a, "Owner", "Corp A")
        headers_b, _ = await register_and_login(ac, email_b, "Owner", "Corp B")
        
        candidate_id = str(uuid.uuid4())
        MOCK_DB["candidates"].append({
            "id": candidate_id,
            "full_name": "GDPR John Doe",
            "email": "john.doe@example.com",
            "role": "Software Engineer",
            "status": "Screening",
            "recruiter_id": tenant_a_id
        })

        res = await ac.delete(f"/api/v1/candidates/{candidate_id}/gdpr-forget", headers=headers_b)
        assert res.status_code in [403, 404]

@pytest.mark.asyncio
async def test_gdpr_forget_non_existent():
    email = f"a_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, email, "Owner", "Corp A")
        res = await ac.delete(f"/api/v1/candidates/{str(uuid.uuid4())}/gdpr-forget", headers=headers)
        assert res.status_code == 404
