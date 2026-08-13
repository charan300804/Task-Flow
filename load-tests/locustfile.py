import random
import uuid
from locust import HttpUser, task, between

class TaskFlowUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Authenticate user and store token."""
        response = self.client.post("/auth/login", data={
            "username": "user@taskflow.io",
            "password": "user123"
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}

    @task(4)
    def submit_ml_prediction_job(self):
        """Simulate submitting ML prediction workload."""
        self.client.post(
            "/api/jobs",
            json={
                "job_type": "ML_PREDICTION",
                "priority": random.randint(1, 10),
                "payload": {
                    "dataset_size": random.choice([500, 1000, 2000]),
                    "num_trees": 30
                },
                "max_retries": 3,
                "timeout_seconds": 120
            },
            headers=self.headers
        )

    @task(3)
    def submit_generic_sleep_job(self):
        """Simulate submitting lightweight sleep task."""
        self.client.post(
            "/api/jobs",
            json={
                "job_type": "GENERIC",
                "priority": random.randint(1, 10),
                "payload": {
                    "duration_seconds": random.choice([1, 2, 3])
                }
            },
            headers=self.headers
        )

    @task(2)
    def submit_cpu_prime_job(self):
        """Simulate submitting math intensive prime number search."""
        self.client.post(
            "/api/jobs",
            json={
                "job_type": "PYTHON_TASK",
                "priority": 8,
                "payload": {
                    "limit": 15000
                }
            },
            headers=self.headers
        )

    @task(5)
    def check_jobs_queue(self):
        """Simulate user querying dashboard jobs list."""
        self.client.get("/api/jobs?page=1&size=20", headers=self.headers)

    @task(2)
    def check_overview_metrics(self):
        """Simulate user viewing dashboard overview stats."""
        self.client.get("/api/metrics/overview", headers=self.headers)
