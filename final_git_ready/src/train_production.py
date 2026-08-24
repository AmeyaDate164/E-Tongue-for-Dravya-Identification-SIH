
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import json

# Configuration
DATA_PATH = "Untitled spreadsheet.csv" # The production file
MODEL_PATH = "models/production_model.pkl"

def train():
    print(f"--- Training Production Model from {DATA_PATH} ---")
    
    # 1. Load Data
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        print(f"Error: {e}")
        return

    print("Columns found:", df.columns.tolist())
    
    # 2. Identify Target and Features
    # Case insensitive search
    cols = {c.lower(): c for c in df.columns}
    
    target_col = cols.get('taste')
    if not target_col:
        print("Error: 'taste' column not found.")
        return
        
    # Features = All numeric columns except taste
    features = [c for c in df.columns if c != target_col and pd.api.types.is_numeric_dtype(df[c])]
    print(f"Features: {features}")
    
    X = df[features]
    y = df[target_col]
    
    # 3. Train Model
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    
    acc = clf.score(X, y)
    print(f"Training Accuracy: {acc:.2%}")
    
    # 4. Save Model & Metadata
    # We need to save the feature names so the app knows what to expect
    model_data = {
        "model": clf,
        "features": features,
        "classes": clf.classes_.tolist()
    }
    
    joblib.dump(model_data, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    
    # 5. Calculate Intensity Weights (Score) for these features
    # Similar to before, we use AUC/Correlation or Random Forest Importance
    # RF Feature Importance is easiest here
    importances = clf.feature_importances_
    weights = {f: float(i) for f, i in zip(features, importances)}
    
    with open("production_weights.json", "w") as f:
        json.dump(weights, f, indent=4)
    print("Feature Weights saved to production_weights.json")

if __name__ == "__main__":
    train()
