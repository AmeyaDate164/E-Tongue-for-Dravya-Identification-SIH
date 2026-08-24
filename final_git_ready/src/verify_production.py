
import joblib
import pandas as pd
import json

MODEL_PATH = "models/production_model.pkl"
WEIGHTS_PATH = "production_weights.json"

def verify_production_logic(*args):
    print(f"\n--- Testing Input: {args} ---")
    
    # 1. Load Model
    try:
        model_data = joblib.load(MODEL_PATH)
        model = model_data["model"]
        features = model_data["features"]
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    if len(args) != len(features):
        print(f"Error: Model expects {len(features)} features ({features}), but received {len(args)} arguments.")
        return

    # 2. Load Weights
    weights = {}
    try:
        with open(WEIGHTS_PATH, "r") as f:
            weights = json.load(f)
    except:
        pass

    # 3. Predict
    # Create DataFrame with exact feature names
    input_data = {}
    for i, feature_name in enumerate(features):
        input_data[feature_name] = args[i]
        
    df = pd.DataFrame([input_data])
    
    # Predict Intensities
    pred_raw = model.predict(df)[0]
    
    # Map to Target Names (stored as 'classes' in the pickle for compatibility)
    target_names = model_data.get("classes", [])
    
    # Output
    print(f"Prediction Raw: {pred_raw}")
    print("Taste Intensities:")
    
    if len(target_names) == len(pred_raw):
        result_dict = {name: val for name, val in zip(target_names, pred_raw)}
        for name, val in result_dict.items():
            print(f"  {name}: {val:.2f}")
            
        # Determine likely dominant taste
        dominant = max(result_dict, key=result_dict.get)
        print(f"\nDominant Taste: {dominant} ({result_dict[dominant]:.2f})")
    else:
        print("Warning: Number of target names does not match number of outputs.")

        
    # Calculate Score (Optional legacy)
    score = 0
    for f in features:
        if f in weights:
            score += weights[f] * input_data[f]
    print(f"Signal Score: {score:.2f}")

if __name__ == "__main__":
    print("Running Acceptance Test logic.")
    
    # Check what features the current model has
    try:
        m = joblib.load(MODEL_PATH)
        features = m['features']
        print(f"Model expects features: {features}")
        
        # Parse CLI args if provided
        import sys
        if len(sys.argv) > 1:
            # sys.argv[0] is script name
            args = [float(arg) for arg in sys.argv[1:]]
            verify_production_logic(*args)
        else:
            print("No arguments provided. Using dummy inputs.")
            dummy_args = [100.0] * len(features)
            verify_production_logic(*dummy_args)
            
    except Exception as e:
        print(f"Error: {e}")
