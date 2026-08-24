
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import json

def calculate_weights(filepath="TasteData.csv"):
    print(f"--- Calculating Signal Weights from {filepath} ---")
    
    # Load Data
    # The file has a header on row 2 (index 1) effectively?
    # Line 1: ,Sour...
    # Line 2: Sr. No., reagent...
    # Let's read with header=1 (row 2) to get the proper names
    df = pd.read_csv(filepath, header=1)
    
    # Identify Target
    # User said 0 and 1 in 'taste' column
    target_col = 'taste'
    if target_col not in df.columns:
        # Try to find it case-insensitive
        for c in df.columns:
            if str(c).lower() == 'taste':
                target_col = c
                break
    
    if target_col not in df.columns:
        print("Error: 'taste' column not found.")
        return
        
    print(f"Target Column: {target_col}")
    
    # Identify Features
    # All numeric columns except target and 'Sr. No.'
    # And we should only consider columns that actually have data
    feature_cols = []
    for col in df.columns:
        if col == target_col: continue
        if "Sr. No." in str(col): continue
        if "Unnamed" in str(col): continue
        
        # Check if numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            # Check if it has enough data (not all NaN)
            if df[col].notna().sum() > 5:
                feature_cols.append(col)
                
    print(f"Features Analyzing: {feature_cols}")
    
    # Calculate AUCs
    if df[feature_cols].isnull().any().any():
        print("Note: Filling missing values with 0 for AUC calculation.")
        df[feature_cols] = df[feature_cols].fillna(0)

    aucs = {}
    for col in feature_cols:
        temp_df = df[[col, target_col]] # No dropna, we filled 0
        y_true = temp_df[target_col]
        y_scores = temp_df[col]
        
        # Check binary
        if len(y_true.unique()) < 2:
            print(f"Skipping {col}: Not enough classes (needs 0 and 1).")
            continue
            
        try:
            auc = roc_auc_score(y_true, y_scores)
            # If AUC < 0.5, it means the correlation is negative (feature is lower for class 1).
            # Usually for intensity we expect High Value = Taste.
            # But we'll take the raw AUC or max(auc, 1-auc)? 
            # User logic was simple AUC. We'll stick to that.
            if auc < 0.5:
                auc = 1.0 - auc # Flip it so it represents predictive power magnitude
                
            aucs[col] = auc
            print(f"  {col}: AUC = {auc:.4f}")
        except Exception as e:
            print(f"  Error {col}: {e}")
            
    # Calculate Weights
    total_auc = sum(aucs.values())
    if total_auc == 0:
        print("Total AUC is 0. Cannot compute weights.")
        return
        
    weights = {col: auc / total_auc for col, auc in aucs.items()}
    
    print("\nCalculated Weights:")
    for k, v in weights.items():
        print(f"  {k}: {v:.4f}")
        
    # Save
    with open("weights.json", "w") as f:
        json.dump(weights, f, indent=4)
    print("Saved to weights.json")

if __name__ == "__main__":
    calculate_weights()
