import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.main import app

def test_health_check_healthy():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data

def test_health_check_unhealthy():
    # Mock get_supabase to raise an error
    with patch("db.supabase_client.get_supabase") as mock_get_supabase:
        mock_get_supabase.side_effect = Exception("Connection timed out")
        
        with TestClient(app) as client:
            res = client.get("/health")
            assert res.status_code == 503
            data = res.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "unreachable"
            assert "Connection timed out" in data["error"]
            assert "timestamp" in data

def test_liveness_check():
    # Keep GET / as simple liveness check
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "hireiq api operational"
        assert "version" in data
