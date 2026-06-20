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
    if role == "Owner":
        user_record["plan"] = "pro"
    
    login_res = await ac.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_record["id"]

@pytest.mark.asyncio
async def test_get_jobs_seeded():
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, owner_email, "Owner", "Owner Corp")
        res = await ac.get("/api/v1/jobs", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 4

@pytest.mark.asyncio
async def test_create_job():
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, owner_email, "Owner", "Owner Corp")
        new_job_data = {
            "title": "Staff Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers, json=new_job_data)
        assert res.status_code == 201
        assert res.json()["title"] == "Staff Backend Engineer"

@pytest.mark.asyncio
async def test_update_job():
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, owner_email, "Owner", "Owner Corp")
        
        # Create a job first
        new_job_data = {
            "title": "Staff Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers, json=new_job_data)
        job_id = res.json()["id"]

        updated_data = {**new_job_data, "title": "Updated Staff Backend Engineer"}
        res_put = await ac.put(f"/api/v1/jobs/{job_id}", headers=headers, json=updated_data)
        assert res_put.status_code == 200
        assert res_put.json()["title"] == "Updated Staff Backend Engineer"

@pytest.mark.asyncio
async def test_delete_job():
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, owner_email, "Owner", "Owner Corp")
        
        # Create a job first
        new_job_data = {
            "title": "Staff Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers, json=new_job_data)
        job_id = res.json()["id"]

        res_delete = await ac.delete(f"/api/v1/jobs/{job_id}", headers=headers)
        assert res_delete.status_code == 200
        assert res_delete.json() == {"status": "deleted"}

        res_get = await ac.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert res_get.status_code == 404

@pytest.mark.asyncio
async def test_rbac_jobs_forbidden():
    viewer_email = f"viewer_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, viewer_email, "Viewer", "Corp")
        new_job_data = {
            "title": "Staff Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers, json=new_job_data)
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_tenant_isolation_jobs():
    email_a = f"a_{uuid.uuid4().hex[:6]}@example.com"
    email_b = f"b_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers_a, _ = await register_and_login(ac, email_a, "Owner", "Corp A")
        headers_b, _ = await register_and_login(ac, email_b, "Owner", "Corp B")

        # Create job in Tenant A
        new_job_data = {
            "title": "A's Job",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers_a, json=new_job_data)
        job_id = res.json()["id"]

        # Tenant B tries to get it
        res_get = await ac.get(f"/api/v1/jobs/{job_id}", headers=headers_b)
        assert res_get.status_code in [403, 404]

@pytest.mark.asyncio
async def test_job_matches_empty():
    owner_email = f"owner_{uuid.uuid4().hex[:6]}@example.com"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        headers, _ = await register_and_login(ac, owner_email, "Owner", "Owner Corp")
        
        # Create a job first
        new_job_data = {
            "title": "Staff Backend Engineer",
            "department": "Engineering",
            "location": "Remote",
            "employment_type": "Full-time",
            "experience_required": 5,
            "description": "Lead design of our core DB.",
            "required_skills": "Python,FastAPI,PostgreSQL",
            "status": "Open"
        }
        res = await ac.post("/api/v1/jobs", headers=headers, json=new_job_data)
        job_id = res.json()["id"]

        res_matches = await ac.get(f"/api/v1/jobs/{job_id}/matches", headers=headers)
        assert res_matches.status_code == 200
        assert res_matches.json() == []
