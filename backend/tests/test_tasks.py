import pytest
from app.tasks.ml_prediction import execute_ml_prediction_task
from app.tasks.generic import execute_cpu_prime_task, execute_sleep_task, execute_data_processing_task

def test_execute_cpu_prime_task():
    res = execute_cpu_prime_task({"limit": 1000})
    assert res["prime_count"] == 168
    assert res["largest_prime"] == 997
    assert res["execution_time_ms"] >= 0

def test_execute_data_processing_task():
    res = execute_data_processing_task({"items_count": 100})
    assert res["items_processed"] == 100
    assert len(res["group_stats"]) == 5

def test_execute_ml_prediction_task(mocker=None):
    payload = {"dataset_size": 200, "num_trees": 10, "model": "RandomForestRegressor"}
    res = execute_ml_prediction_task("test-job-uuid-123", payload)
    assert res["prediction_count"] == 200
    assert res["model"] == "RandomForestRegressor"
    assert "mean_predicted_price" in res["summary"]
    assert res["execution_time_ms"] > 0
