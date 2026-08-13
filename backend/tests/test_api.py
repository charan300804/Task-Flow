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

def test_unauthorized_job_submission():
    res = client.post("/api/jobs", json={
        "job_type": "GENERIC",
        "priority": 5,
        "payload": {}
    })
    assert res.status_code == 401
