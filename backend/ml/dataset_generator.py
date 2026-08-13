import os
import pandas as pd
import numpy as np

def generate_dataset(output_path: str = "ml/datasets/houses.csv", num_samples: int = 5000):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.random.seed(42)
    
    square_feet = np.random.normal(2200, 600, num_samples).clip(700, 7000)
    bedrooms = np.random.randint(1, 6, num_samples)
    bathrooms = np.random.randint(1, 5, num_samples)
    age = np.random.randint(0, 60, num_samples)
    location_score = np.random.uniform(1.0, 10.0, num_samples)

    base_price = (
        square_feet * 195 +
        bedrooms * 18000 +
        bathrooms * 28000 -
        age * 1100 +
        location_score * 32000 +
        np.random.normal(0, 20000, num_samples)
    )

    df = pd.DataFrame({
        "square_feet": square_feet.round(1),
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "age": age,
        "location_score": location_score.round(2),
        "price": base_price.round(2)
    })

    df.to_csv(output_path, index=False)
    print(f"Generated housing dataset with {num_samples} records at {output_path}")

if __name__ == "__main__":
    generate_dataset()
