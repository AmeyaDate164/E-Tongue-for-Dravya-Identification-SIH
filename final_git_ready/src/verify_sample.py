
import pandas as pd
import numpy as np
from model_trainer import TasteModel
import json

# Inputs
sample = {
    "reagent 1 (mo)": 96.3,
    "reagent 2": 133.06,  # Note: "reagent 2" vs "reagent 2 (fecl3)". Model uses "reagent 2"?
    # checking FEATURES in app.py: "reagent 2", "reagent 3"
    "reagent 3": 73.45
}

# The model features in app.py are:
# "reagent 1 (mo)", "reagent 2", "reagent 3"
# The weights.json keys might be from TasteData.csv
# Let's inspect weights.json first or handle both keys.

def verify():
    print(f"--- Verifying Sample: {sample} ---")
    
    # 1. Load Model
    try:
        model = TasteModel.load("models/taste_model.pkl")
        print("Model loaded.")
    except:
        print("Error loading model.")
        return

    # 2. Load Weights
    weights = {}
    try:
        with open("weights.json", "r") as f:
            weights = json.load(f)
        print("Weights loaded.")
    except:
        print("Error loading weights.")

    # 3. Align Features
    # The Model was trained on `data_loader.py` output. 
    # Data loader likely normalized "reagent 2 (fecl3)" -> "reagent 2" or kept original?
    # Let's check the FEATURE list in app.py again to be sure. 
    # Logic in app.py: FEATURES = ["reagent 1 (mo)", "reagent 2", "reagent 3", ...]
    # So we must map inputs to these keys.
    
    input_data = {
        "reagent 1 (mo)": sample["reagent 1 (mo)"],
        "reagent 2": sample["reagent 2"],
        "reagent 3": sample["reagent 3"],
        # Fill others with 0
        "reagent 4": 0, "G2": 0, "B2": 0, "R3": 0, "G3": 0, "B3": 0, "R4": 0, "G4": 0, 
        "reagent 5": 0, "reagent 6": 0, "reagent 7": 0, 
        "reagent 8": 0, "reagent 9": 0, "reagent 10": 0
    }
    
    # DataFrame
    df = pd.DataFrame([input_data])
    
    # 4. Predict Taste
    pred = model.predict(df.iloc[0])
    print(f"\nPREDICTION: {pred['predicted_taste']}")
    print(f"CONFIDENCE: {pred['confidence']*100:.2f}%")
    
    # 5. Calculate Score
    # Weights keys come from TasteData.csv which had: 'reagent 2 (fecl3)'
    # We need to map our sample values to those keys roughly
    s_score = 0
    
    # Map for scoring
    # We have values for R1, R2, R3.
    # We look at weights.json keys.
    for k, w in weights.items():
        val = 0
        if "reagent 1" in k: val = sample["reagent 1 (mo)"]
        elif "reagent 2" in k: val = sample["reagent 2"]
        elif "reagent 3" in k: val = sample["reagent 3"]
        
        s_score += w * val
        print(f"  > Weight '{k}' ({w:.4f}) * Value ({val}) = {w * val:.2f}")

    print(f"\nSIGNAL INTENSITY SCORE: {s_score:.2f}")
    
    # Interpretation
    if pred['predicted_taste'] == 'Sour' and pred['confidence'] > 0.5:
        print("\nVERDICT: YES, THIS IS SOUR.")
    else:
        print(f"\nVERDICT: NO, looks like {pred['predicted_taste']}.")

if __name__ == "__main__":
    verify()
