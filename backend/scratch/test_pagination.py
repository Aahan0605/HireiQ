import sys
from pathlib import Path

# Add backend dir to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app
from api.core.rbac import require_tenant

# Mock require_tenant dependency to return a dummy organization id
async def mock_require_tenant():
    return "dummy-tenant-id"

app.dependency_overrides[require_tenant] = mock_require_tenant

client = TestClient(app)

def test_pagination():
    # Seed demo candidates first
    seed_resp = client.post("/api/v1/candidates/seed-demo")
    assert seed_resp.status_code == 200, f"Seeding failed: {seed_resp.text}"
    print("Seed database response:", seed_resp.json())

    # Test normal pagination
    response = client.get("/api/v1/candidates?page=1&limit=2")
    assert response.status_code == 200, f"Failed: {response.text}"
    res_data = response.json()
    assert "data" in res_data
    assert "total" in res_data
    assert "page" in res_data
    assert "limit" in res_data
    assert "pages" in res_data
    assert "has_next" in res_data
    assert "has_prev" in res_data
    assert res_data["page"] == 1
    assert res_data["limit"] == 2
    
    # Test status filtering
    response_status = client.get("/api/v1/candidates?status=Interviewing")
    assert response_status.status_code == 200
    res_status = response_status.json()
    for cand in res_status["data"]:
        assert cand["status"] == "Interviewing"

    # Test search filtering
    response_search = client.get("/api/v1/candidates?search=Sofia")
    assert response_search.status_code == 200
    res_search = response_search.json()
    for cand in res_search["data"]:
        assert "sofia" in cand["name"].lower() or "sofia" in cand["role"].lower()

    print("Candidate Pagination & Filter tests passed successfully!")
    print("Sample response:", res_data)

if __name__ == "__main__":
    test_pagination()
