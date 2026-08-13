import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

def train_and_save_model(data_path: str = "ml/datasets/houses.csv", model_output: str = "ml/models/housing_model.joblib"):
    if not os.path.exists(data_path):
        from ml.dataset_generator import generate_dataset
        generate_dataset(data_path)

    df = pd.read_csv(data_path)
    X = df.drop(columns=["price"])
    y = df["price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    joblib.dump(model, model_output)
    print(f"Model trained successfully. MSE: {mse:.2f}, R2: {r2:.4f}. Saved to {model_output}")

if __name__ == "__main__":
    train_and_save_model()
