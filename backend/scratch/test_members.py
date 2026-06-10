import sys
from pathlib import Path
import uuid

# Add parent dir to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app
from api.core.dependencies import get_current_user
from db.session import SessionLocal
from db.models import User, Organization, OrganizationMember

# Create test data
db = SessionLocal()
test_user = db.query(User).filter(User.email == "test_member_manager@example.com").first()
if not test_user:
    test_user = User(
        id=str(uuid.uuid4()),
        email="test_member_manager@example.com",
        hashed_password="dummy_hash",
        role="Admin",
        is_verified=True
    )
    db.add(test_user)
    db.commit()

test_org = db.query(Organization).filter(Organization.name == "Test Org For invites").first()
if not test_org:
    test_org = Organization(
        id=str(uuid.uuid4()),
        name="Test Org For invites",
        billing_tier="Free"
    )
    db.add(test_org)
    db.commit()

test_member = db.query(OrganizationMember).filter(
    OrganizationMember.user_id == test_user.id,
    OrganizationMember.organization_id == test_org.id
).first()
if not test_member:
    test_member = OrganizationMember(
        id=str(uuid.uuid4()),
        organization_id=test_org.id,
        user_id=test_user.id,
        role="Admin"  # Has Permission.MANAGE_MEMBERS
    )
    db.add(test_member)
    db.commit()

# Copy variables out of session before closing
test_user_id = test_user.id
test_user_email = test_user.email
test_user_role = test_user.role
test_org_id = test_org.id
test_org_name = test_org.name

db.close()

# Mock get_current_user to return this test user
async def mock_get_current_user():
    return {
        "id": test_user_id,
        "email": test_user_email,
        "role": test_user_role
    }

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

def test_members():
    headers = {"X-Tenant-ID": test_org_id}

    # 1. Test invite member
    invite_payload = {
        "email": "invitee@example.com",
        "role": "Recruiter"
    }
    response_invite = client.post("/api/v1/members/invite", json=invite_payload, headers=headers)
    assert response_invite.status_code == 200, f"Invite failed: {response_invite.text}"
    invite_data = response_invite.json()
    assert "token" in invite_data
    assert "message" in invite_data
    print("Invitation generated successfully:", invite_data)

    # 2. Test list members (will have test_user)
    response_list = client.get("/api/v1/members", headers=headers)
    assert response_list.status_code == 200, f"List failed: {response_list.text}"
    members_data = response_list.json()
    assert len(members_data) >= 1
    print("Workspace members list:", members_data)

    # 3. Test delete non-existent member
    response_delete = client.delete("/api/v1/members/non-existent-id", headers=headers)
    assert response_delete.status_code == 404
    print("Delete non-existent member returned 404 as expected.")

    # 4. Test remove member
    # Let's add another test member first so we can delete them
    db = SessionLocal()
    to_delete_user = User(
        id=str(uuid.uuid4()),
        email="to_delete@example.com",
        hashed_password="dummy",
        is_verified=True
    )
    to_delete_member = OrganizationMember(
        id=str(uuid.uuid4()),
        organization_id=test_org_id,
        user_id=to_delete_user.id,
        role="Recruiter"
    )
    db.add(to_delete_user)
    db.add(to_delete_member)
    db.commit()
    
    to_delete_member_id = to_delete_member.id
    db.close()

    response_delete_real = client.delete(f"/api/v1/members/{to_delete_member_id}", headers=headers)
    assert response_delete_real.status_code == 200
    print("Delete member returned 200 as expected.")

    print("All Team Member Invitation endpoint tests passed successfully!")

if __name__ == "__main__":
    test_members()
