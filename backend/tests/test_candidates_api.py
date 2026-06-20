import pytest
import uuid
import httpx
from api.main import app
from conftest import MOCK_DB

@pytest.mark.asyncio
async def test_candidates_api():
    # 1. Test register and login
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    password = "Password123!"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Register recruiter
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "role": "Owner",
            "company": "Test Company",
            "full_name": "Test User"
        })
        assert reg_res.status_code == 201
        
        # Verify the user in MOCK_DB so they can sign in
        user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
        user_record["is_verified"] = True
        
        # Login
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test unauthenticated calls to GET /candidates return 401
        unauth_res = await ac.get("/api/v1/candidates")
        assert unauth_res.status_code == 401
        
        # 3. Test authenticated calls to GET /candidates return 200 with correct JSON shape
        auth_res = await ac.get("/api/v1/candidates", headers=headers)
        assert auth_res.status_code == 200
        res_data = auth_res.json()
        assert "data" in res_data
        assert "total" in res_data
        
        # Create a candidate for our tenant A
        tenant_id = user_record["id"]
        MOCK_DB["scoring_weights"].append({
            "id": str(uuid.uuid4()),
            "recruiter_id": tenant_id,
            "skills_weight": 0.4,
            "experience_weight": 0.3,
            "education_weight": 0.2,
            "github_weight": 0.1
        })
        
        candidate_id = str(uuid.uuid4())
        candidate_data = {
            "id": candidate_id,
            "name": "Candidate A",
            "email": "cand_a@example.com",
            "role": "Software Engineer",
            "status": "Screening",
            "recruiter_id": tenant_id
        }
        MOCK_DB["candidates"].append(candidate_data)
        
        # Test fetching the list again
        auth_res = await ac.get("/api/v1/candidates", headers=headers)
        assert auth_res.status_code == 200
        res_data = auth_res.json()
        assert res_data["total"] == 1
        assert res_data["data"][0]["id"] == candidate_id
        
        # 4. Test stage updates (PATCH /candidates/{id}/stage) with invalid stage names return 400
        bad_stage_res = await ac.patch(
            f"/api/v1/candidates/{candidate_id}/stage",
            headers=headers,
            json={"stage": "invalid_stage_name"}
        )
        assert bad_stage_res.status_code == 400
        assert "Invalid stage name" in bad_stage_res.json()["detail"]
        
        # Test valid stage update
        good_stage_res = await ac.patch(
            f"/api/v1/candidates/{candidate_id}/stage",
            headers=headers,
            json={"stage": "shortlisted"}
        )
        assert good_stage_res.status_code == 200
        assert good_stage_res.json()["stage"] == "shortlisted"
        
        # 5. Test saving an empty note (POST /candidates/{id}/notes) returns a validation error (400 status code)
        empty_note_res = await ac.post(
            f"/api/v1/candidates/{candidate_id}/notes",
            headers=headers,
            json={
                "author": "Test Author",
                "comment": "",
                "rating": 5
            }
        )
        assert empty_note_res.status_code == 400
        assert "cannot be empty" in empty_note_res.json()["detail"]
        
        # Test whitespace-only note
        ws_note_res = await ac.post(
            f"/api/v1/candidates/{candidate_id}/notes",
            headers=headers,
            json={
                "author": "Test Author",
                "comment": "   ",
                "rating": 5
            }
        )
        assert ws_note_res.status_code == 400
        
        # Test successful note creation
        good_note_res = await ac.post(
            f"/api/v1/candidates/{candidate_id}/notes",
            headers=headers,
            json={
                "author": "Test Author",
                "comment": "This is a great note!",
                "rating": 5
            }
        )
        assert good_note_res.status_code == 200
        assert good_note_res.json()["comment"] == "This is a great note!"
