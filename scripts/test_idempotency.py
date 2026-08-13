import uuid
import requests

API_URL = "http://localhost:8000"

def run_idempotency_test():
    print("=== SCENARIO 5: Idempotency Key Duplicate Submission ===")
    
    login_res = requests.post(f"{API_URL}/auth/login", data={"username": "user@taskflow.io", "password": "user123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    idempotency_key = f"test-key-{uuid.uuid4().hex[:8]}"
    payload = {
        "job_type": "ML_PREDICTION",
        "priority": 7,
        "payload": {"dataset_size": 500, "num_trees": 10},
        "idempotency_key": idempotency_key
    }

    # First Submission
    res1 = requests.post(f"{API_URL}/api/jobs", json=payload, headers=headers)
    job1 = res1.json()
    print(f"First Submission -> Created Job ID: {job1['id']}")

    # Second Submission with SAME idempotency key
    res2 = requests.post(f"{API_URL}/api/jobs", json=payload, headers=headers)
    job2 = res2.json()
    print(f"Second Submission -> Returned Job ID: {job2['id']}")

    assert job1['id'] == job2['id'], "Idempotency test failed! Created duplicate job!"
    print("SUCCESS: Idempotency key verified! Duplicate request safely returned original job instance.")

if __name__ == "__main__":
    run_idempotency_test()
