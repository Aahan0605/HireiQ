import pytest
import uuid
import httpx
from api.main import app
from api.core.security import create_access_token
from db.supabase_client import save_candidate
from api.routes.jobs import save_job
from conftest import MOCK_DB

@pytest.mark.asyncio
async def test_tenant_isolation():
    # 1. Setup: Programmatically create two separate tenants/organizations (Tenant A, Tenant B)
    tenant_a_id = str(uuid.uuid4())
    tenant_b_id = str(uuid.uuid4())

    # Populate mock recruiters database
    MOCK_DB["recruiters"].extend([
        {
            "id": tenant_a_id,
            "email": "tenant_a@example.com",
            "hashed_password": "hashed_pwd_a",  # pragma: allowlist secret
            "role": "Owner",
            "company": "Company A",
            "is_verified": True,
            "plan": "free"
        },
        {
            "id": tenant_b_id,
            "email": "tenant_b@example.com",
            "hashed_password": "hashed_pwd_b",  # pragma: allowlist secret
            "role": "Owner",
            "company": "Company B",
            "is_verified": True,
            "plan": "free"
        }
    ])

    # Populate mock scoring weights
    MOCK_DB["scoring_weights"].extend([
        {
            "id": str(uuid.uuid4()),
            "recruiter_id": tenant_a_id,
            "skills_weight": 0.4,
            "experience_weight": 0.3,
            "education_weight": 0.2,
            "github_weight": 0.1
        },
        {
            "id": str(uuid.uuid4()),
            "recruiter_id": tenant_b_id,
            "skills_weight": 0.4,
            "experience_weight": 0.3,
            "education_weight": 0.2,
            "github_weight": 0.1
        }
    ])

    # Generate JWT access tokens
    token_a = create_access_token(tenant_a_id)
    token_b = create_access_token(tenant_b_id)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 2. Tenant A creates a candidate directly in the database
    candidate_a_id = str(uuid.uuid4())
    candidate_a_data = {
        "id": candidate_a_id,
        "name": "Alice Chen",
        "email": "alice.chen@example.com",
        "role": "Senior Frontend Engineer",
        "status": "Screening",
        "recruiter_id": tenant_a_id
    }
    await save_candidate(candidate_a_data, tenant_a_id)

    # 3. Tenant A creates a job directly in the database
    job_a_id = str(uuid.uuid4())
    job_a_data = {
        "id": job_a_id,
        "title": "Senior Frontend Developer",
        "description": "Awesome React position",
        "required_skills": "React,TypeScript",
        "min_experience": 3,
        "recruiter_id": tenant_a_id
    }
    await save_job(job_a_data, tenant_a_id)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Test 1: Tenant B's token calls GET /candidates/{tenant_A_candidate_id}
        # assert this returns 403 or 404, NEVER 200 with Tenant A's data
        res = await ac.get(f"/api/v1/candidates/{candidate_a_id}", headers=headers_b)
        assert res.status_code in [403, 404], f"Expected 403/404, got {res.status_code}"
        assert "Alice Chen" not in res.text

        # Test 2: Tenant B's token calls GET /candidates (list)
        # assert Tenant A's candidate does NOT appear anywhere in the response
        res = await ac.get("/api/v1/candidates", headers=headers_b)
        assert res.status_code == 200
        candidates = res.json()
        # candidate list may return an object with "data" list, or a raw list
        candidate_list = candidates.get("data", candidates) if isinstance(candidates, dict) else candidates
        candidate_ids = [c["id"] for c in candidate_list]
        assert candidate_a_id not in candidate_ids, "Tenant A's candidate leaked into Tenant B's list!"

        # Test 3: Tenant B's token calls PATCH /candidates/{tenant_A_id}/stage
        # assert this is rejected, not silently applied
        res = await ac.patch(
            f"/api/v1/candidates/{candidate_a_id}/stage",
            headers=headers_b,
            json={"stage": "shortlisted"}
        )
        assert res.status_code in [403, 404], f"Expected 403/404 on stage update, got {res.status_code}"

        # Test 4: Repeat the same pattern for GET /jobs and GET /jobs/{id}
        # confirm Tenant B cannot read or list Tenant A's jobs
        res = await ac.get(f"/api/v1/jobs/{job_a_id}", headers=headers_b)
        assert res.status_code in [403, 404], f"Expected 403/404 for job fetch, got {res.status_code}"

        res = await ac.get("/api/v1/jobs", headers=headers_b)
        assert res.status_code == 200
        jobs_list = res.json()
        job_ids = [j["id"] for j in jobs_list]
        assert job_a_id not in job_ids, "Tenant A's job leaked into Tenant B's list!"

        # Test 5: Repeat for GET /reports/candidates/{id}/pdf
        # confirm Tenant B cannot download Tenant A's candidate PDF
        res = await ac.get(f"/api/v1/reports/candidates/{candidate_a_id}/pdf", headers=headers_b)
        assert res.status_code in [403, 404], f"Expected 403/404 for PDF report download, got {res.status_code}"
