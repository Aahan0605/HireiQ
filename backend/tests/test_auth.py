import pytest
import uuid
import httpx
from datetime import datetime, timedelta, timezone
from api.main import app
from conftest import MOCK_DB

@pytest.fixture(autouse=True)
def clean_recruiters():
    MOCK_DB["recruiters"].clear()

@pytest.mark.asyncio
async def test_auth_login_lockout():
    email = f"lockout_{uuid.uuid4().hex[:6]}@example.com"
    password = "CorrectPassword123!"  # pragma: allowlist secret
    wrong_password = "WrongPassword123!"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register a user
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "role": "Owner",
            "company": "Lockout Corp",
            "full_name": "Lockout User"
        })
        assert reg_res.status_code == 201
        
        # Verify the user
        user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
        user_record["is_verified"] = True
        
        # 2. Perform 4 failed login attempts
        for i in range(4):
            login_res = await ac.post("/api/v1/auth/login", json={
                "email": email,
                "password": wrong_password
            })
            assert login_res.status_code == 401
            assert login_res.json()["detail"] == "Incorrect email or password"
            # Verify counter increment
            assert user_record.get("failed_login_attempts", 0) == i + 1
            assert user_record.get("locked_until") is None

        # 3. Perform 5th failed login attempt -> lockout triggers
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": wrong_password
        })
        assert login_res.status_code == 400
        assert "Account temporarily locked" in login_res.json()["detail"]
        assert user_record.get("failed_login_attempts", 0) == 5
        assert user_record.get("locked_until") is not None
        
        # 4. Attempt 6th login with correct password -> still locked out
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 400
        assert "Account temporarily locked" in login_res.json()["detail"]
        
        # 5. Reset lockout / expire lockout manually by shifting timestamp to past
        user_record["locked_until"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        
        # 6. Login with correct password -> succeeds and resets attempts
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()
        assert user_record.get("failed_login_attempts", 0) == 0
        assert user_record.get("locked_until") is None

@pytest.mark.asyncio
async def test_forgot_and_reset_password():
    email = f"forgot_test_{uuid.uuid4().hex[:6]}@example.com"
    password = "CorrectPassword123!"  # pragma: allowlist secret
    new_password = "NewPassword123!"  # pragma: allowlist secret
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register a user
        reg_res = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "role": "Owner",
            "company": "Forgot Corp",
            "full_name": "Forgot User"
        })
        assert reg_res.status_code == 201
        
        # Verify the user is registered
        user_record = next(u for u in MOCK_DB["recruiters"] if u["email"] == email)
        assert user_record is not None
        
        # Make the user verified so we can test login later
        user_record["is_verified"] = True
        
        # 2. Call forgot-password endpoint
        forgot_res = await ac.post("/api/v1/auth/forgot-password", json={
            "email": email
        })
        assert forgot_res.status_code == 200
        assert forgot_res.json()["message"] == "If that email exists, a reset link has been sent."
        
        # 3. Verify token was created
        assert user_record.get("password_reset_token") is not None
        assert user_record.get("password_reset_expires") is not None
        token = user_record["password_reset_token"]
        
        # 4. Call reset-password endpoint with invalid token -> fails
        reset_res = await ac.post("/api/v1/auth/reset-password", json={
            "token": "invalid_token",
            "new_password": new_password
        })
        assert reset_res.status_code == 400
        assert "Invalid or expired reset token." in reset_res.json()["detail"]
        
        # 5. Call reset-password with valid token -> succeeds
        reset_res = await ac.post("/api/v1/auth/reset-password", json={
            "token": token,
            "new_password": new_password
        })
        assert reset_res.status_code == 200
        assert reset_res.json()["message"] == "Password reset successfully. You can now sign in."
        
        # 6. Verify token is cleared in DB
        assert user_record.get("password_reset_token") is None
        assert user_record.get("password_reset_expires") is None
        
        # 7. Attempt login with old password -> fails
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_res.status_code == 401
        
        # 8. Attempt login with new password -> succeeds
        login_res = await ac.post("/api/v1/auth/login", json={
            "email": email,
            "password": new_password
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

