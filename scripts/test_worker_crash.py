import time
import requests

API_URL = "http://localhost:8000"

def run_worker_crash_scenario():
    print("=== SCENARIO 1: Worker Crash & Fault Tolerance Recovery ===")
    
    # 1. Login
    login_res = requests.post(f"{API_URL}/auth/login", data={"username": "admin@taskflow.io", "password": "admin123"})
    if login_res.status_code != 200:
        print("Failed to authenticate with TaskFlow API")
        return
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check active workers
    workers_res = requests.get(f"{API_URL}/api/workers", headers=headers)
    print(f"Active Worker Nodes: {len(workers_res.json())}")

    # 3. Submit long sleep job
    job_res = requests.post(
        f"{API_URL}/api/jobs",
        json={
            "job_type": "GENERIC",
            "priority": 10,
            "payload": {"duration_seconds": 30},
            "max_retries": 3
        },
        headers=headers
    )
    job = job_res.json()
    job_id = job["id"]
    print(f"Submitted Job {job_id} with priority P10")

    print("Worker failure scenario ready. In Docker environment, run `docker stop taskflow-worker-1` to simulate worker crash.")
    print("The Scheduler Monitor daemon will detect heartbeat timeout (>15s), mark worker UNHEALTHY, and recover orphan job.")

if __name__ == "__main__":
    run_worker_crash_scenario()
