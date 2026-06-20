import pytest
import uuid
import httpx
from unittest.mock import patch
from api.main import app
from conftest import MOCK_DB

@pytest.fixture(autouse=True)
def clean_db():
    MOCK_DB["recruiters"].clear()
    MOCK_DB["candidates"].clear()
    MOCK_DB["jobs"].clear()
    MOCK_DB["scoring_weights"].clear()

@pytest.mark.asyncio
async def test_quota_incremented_on_success():
    email = f"success_{uuid.uuid4().hex[:6]}@example.com"
    password = "Password123!"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Register recruiter
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "role": "Owner",
            "company": "Success Corp",
            "full_name": "Success User"
        })
        assert reg_res.status_code == 201
        
        user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
        user_record["is_verified"] = True
        user_record["cv_upload_count"] = 0
        
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock compute_full_candidate_score to return successfully
        mock_score = {
            "final_score": 90,
            "resume_features": {
                "experience_years": 5,
                "skills": ["Python"],
                "role": "Software Engineer",
                "education_level": "masters"
            },
            "insights": {
                "completeness_score": 90,
                "ats_score": 85,
                "ai_summary": {
                    "strengths": [],
                    "gaps": [],
                    "concerns": [],
                    "executive_summary": "Good."
                }
            }
        }
        
        with patch("api.routes.candidates.compute_full_candidate_score", return_value=mock_score):
            # Upload a valid resume file (e.g. resume.txt)
            files = {"file": ("resume.txt", b"dummy content", "text/plain")}
            res = await ac.post("/api/v1/candidates/upload-resume", headers=headers, files=files)
            assert res.status_code == 202
            
            # Verify that recruiter's cv_upload_count incremented to 1
            assert user_record["cv_upload_count"] == 1

@pytest.mark.asyncio
async def test_quota_not_incremented_on_failure():
    email = f"fail_{uuid.uuid4().hex[:6]}@example.com"
    password = "Password123!"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # Register recruiter
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "role": "Owner",
            "company": "Fail Corp",
            "full_name": "Fail User"
        })
        assert reg_res.status_code == 201
        
        user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
        user_record["is_verified"] = True
        user_record["cv_upload_count"] = 0
        
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock compute_full_candidate_score to fail by raising an exception
        with patch("api.routes.candidates.compute_full_candidate_score", side_effect=Exception("Mock Parser Crash")):
            files = {"file": ("resume.txt", b"dummy content", "text/plain")}
            res = await ac.post("/api/v1/candidates/upload-resume", headers=headers, files=files)
            # The upload endpoint returns 202 (Accepted) immediately after queuing the task
            assert res.status_code == 202
            
            # Verify that recruiter's cv_upload_count did NOT increment
            assert user_record["cv_upload_count"] == 0
