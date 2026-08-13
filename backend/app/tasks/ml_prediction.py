import time
import uuid
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.ensemble import RandomForestRegressor
from app.core.storage import storage_client

logger = logging.getLogger(__name__)

def execute_ml_prediction_task(job_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a real ML Prediction pipeline (House Price Prediction).
    - Accepts payload parameters: dataset_size, num_trees, target_region
    - Trains or uses lightweight RandomForest model
    - Computes batch predictions
    - Uploads prediction result artifact to MinIO Object Storage
    - Returns structured metadata dictionary
    """
    start_time = time.time()
    num_samples = payload.get("dataset_size", 1200)
    num_trees = payload.get("num_trees", 50)
    model_name = payload.get("model", "RandomForestRegressor")

    # Generate synthetic housing dataset for prediction demonstration
    np.random.seed(42)
    square_feet = np.random.normal(2000, 500, num_samples).clip(600, 6000)
    bedrooms = np.random.randint(1, 6, num_samples)
    bathrooms = np.random.randint(1, 5, num_samples)
    age = np.random.randint(0, 50, num_samples)
    location_score = np.random.uniform(1.0, 10.0, num_samples)

    # Ground truth formula with noise
    base_price = (
        square_feet * 180 +
        bedrooms * 15000 +
        bathrooms * 25000 -
        age * 1200 +
        location_score * 30000 +
        np.random.normal(0, 25000, num_samples)
    )

    X = pd.DataFrame({
        "square_feet": square_feet,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "age": age,
        "location_score": location_score
    })
    y = base_price

    # Train model
    model = RandomForestRegressor(n_estimators=num_trees, random_state=42)
    model.fit(X, y)

    # Generate predictions
    predictions = model.predict(X)
    execution_time_ms = int((time.time() - start_time) * 1000)

    # Feature Importance
    feature_importances = dict(zip(X.columns, model.feature_importances_.round(4).tolist()))

    # Summary statistics
    result_data = {
        "job_id": str(job_id),
        "model": model_name,
        "num_trees": num_trees,
        "prediction_count": len(predictions),
        "execution_time_ms": execution_time_ms,
        "metrics": {
            "mean_predicted_price": float(np.mean(predictions)),
            "median_predicted_price": float(np.median(predictions)),
            "min_predicted_price": float(np.min(predictions)),
            "max_predicted_price": float(np.max(predictions)),
            "std_dev": float(np.std(predictions)),
        },
        "feature_importances": feature_importances,
        "sample_predictions": [
            {
                "id": i + 1,
                "square_feet": round(float(square_feet[i]), 1),
                "bedrooms": int(bedrooms[i]),
                "bathrooms": int(bathrooms[i]),
                "predicted_price": round(float(predictions[i]), 2)
            }
            for i in range(min(15, num_samples))
        ]
    }

    # Upload to MinIO object storage
    object_key = f"ml_results/job_{job_id}_result.json"
    result_location = storage_client.upload_json(object_key, result_data)

    return {
        "job_id": str(job_id),
        "prediction_count": len(predictions),
        "model": model_name,
        "execution_time_ms": execution_time_ms,
        "result_location": result_location,
        "object_key": object_key,
        "summary": result_data["metrics"]
    }
