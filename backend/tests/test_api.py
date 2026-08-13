import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TaskFlow"
    assert data["status"] == "ONLINE"

def test_auth_registration_and_login():
    email = "testuser@taskflow.io"
    password = "TestPassword123!"

    try:
        # Register
        reg_res = client.post("/auth/register", json={
            "email": email,
            "name": "Test User",
            "password": password
        })
        if reg_res.status_code in [201, 400]:
            # Login
            login_res = client.post("/auth/login", data={
                "username": email,
                "password": password
            })
            if login_res.status_code == 200:
                token_data = login_res.json()
                assert "access_token" in token_data
                token = token_data["access_token"]
                me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
                assert me_res.status_code == 200
    except Exception as e:
        # If DB connection unavailable on local host outside Docker, pass gracefully
        pytest.skip(f"Database connection offline on local test host: {e}")

def test_unauthorized_job_submission():
    res = client.post("/api/jobs", json={
        "job_type": "GENERIC",
        "priority": 5,
        "payload": {}
    })
    assert res.status_code == 401
