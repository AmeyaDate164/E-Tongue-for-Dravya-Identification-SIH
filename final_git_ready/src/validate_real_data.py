
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

def validate_real():
    print("--- Validating on REAL Data (TasteData.csv) ---")
    
    # 1. Load Data
    try:
        # Header is on row 2 (index 1) based on inspection
        df = pd.read_csv("TasteData.csv", header=1)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 2. Preprocess
    # Target: 'taste' (1 = Sour, 0 = Non-Sour)
    # Features: 'reagent 1 (mo)', 'reagent 2 (fecl3)', 'reagent 3 (bromo)'
    # Note: Column names might have spaces
    
    target_col = 'taste'
    # Find exact col names
    cols = df.columns
    r1 = [c for c in cols if 'reagent 1' in str(c).lower()][0]
    r2 = [c for c in cols if 'reagent 2' in str(c).lower()][0]
    r3 = [c for c in cols if 'reagent 3' in str(c).lower()][0]
    
    features = [r1, r2, r3]
    print(f"Features: {features}")
    
    # Filter valid rows (where we have target and features)
    # Treat NaN features as 0 (no reaction)
    df[features] = df[features].fillna(0)
    
    # Drop rows where target is NaN
    df = df.dropna(subset=[target_col])
    
    X = df[features]
    y = df[target_col]
    
    print(f"Total Samples: {len(X)}")
    print(f"Class Distribution: {y.value_counts().to_dict()}") # Check balance
    
    # 3. Validation Strategy
    # We will use 5-Fold Cross Validation to get a robust estimate
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    
    scoring = ['accuracy', 'precision', 'recall', 'f1']
    scores = cross_validate(clf, X, y, cv=5, scoring=scoring)
    
    print("\n--- Cross-Validation Results (5-Fold) ---")
    print(f"Accuracy:  {scores['test_accuracy'].mean():.2%} (+/- {scores['test_accuracy'].std():.2%})")
    print(f"Precision: {scores['test_precision'].mean():.2%} (+/- {scores['test_precision'].std():.2%})")
    print(f"Recall:    {scores['test_recall'].mean():.2%} (+/- {scores['test_recall'].std():.2%})")
    print(f"F1-Score:  {scores['test_f1'].mean():.2%} (+/- {scores['test_f1'].std():.2%})")
    
    # 4. Detailed Report on Shuffle Split (Hold-out test)
    print("\n--- Detailed Hold-Out Test (30% Test Set) ---")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    
    print(classification_report(y_test, y_pred, target_names=['Non-Sour (0)', 'Sour (1)']))

if __name__ == "__main__":
    validate_real()
