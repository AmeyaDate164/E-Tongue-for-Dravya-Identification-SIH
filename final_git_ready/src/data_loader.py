
import pandas as pd
import numpy as np
import os

def load_data(filepath):
    """
    Smart loader that handles:
    1. Hierarchical CSV (Header row 0=Groups, Row 1=Reagents)
    2. Flat CSV (Header row 0=columns)
    3. Excel
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    print(f"Loading data from {filepath}...")
    
    # Try reading as text to sniff structure
    if filepath.endswith('.csv'):
        # Peek at first few lines
        with open(filepath, 'r') as f:
            lines = [f.readline() for _ in range(5)]
            
        # Check for hierarchical markers
        header_line = lines[0].lower()
        if "sour" in header_line or "astringent" in header_line:
            return load_hierarchical_csv(filepath)
        else:
            return load_csv_data(filepath)
    else:
        # Default to old Excel behavior (which we can route to hierachical if needed)
        try:
             pd.read_excel(filepath) # Just to test
             # We assume Excel is always hierarchical based on previous code
             # But let's reuse the logic
             return load_hierarchical_excel(filepath)
        except:
             return load_hierarchical_csv(filepath)

def load_hierarchical_csv(filepath):
    print("Detected Hierarchical CSV structure.")
    # Read raw
    df_raw = pd.read_csv(filepath, header=None)
    return process_hierarchical_df(df_raw)

def load_hierarchical_excel(filepath):
    print("Detected Hierarchical Excel structure.")
    df_raw = pd.read_excel(filepath, header=None)
    return process_hierarchical_df(df_raw)

def process_hierarchical_df(df_raw):
    # Row 0: Groups (Sour, Astringent)
    # Row 1: Reagent Names
    
    groups_row = df_raw.iloc[0].tolist()
    names_row = df_raw.iloc[1].tolist()
    
    # 1. Identify Blocks
    blocks = {} # Group -> {indices: [], taste_col_idx: None, reagent_col_indices: []}
    
    current_group = None
    ignore_groups = ['nan', 'sr. no.', 'sr. no', '', 'none']
    
    for idx, val in enumerate(groups_row):
        val_str = str(val).lower().strip()
        if val_str not in ignore_groups:
            current_group = str(val).strip()
            
        if current_group:
            if current_group not in blocks:
                blocks[current_group] = {'indices': []}
            blocks[current_group]['indices'].append(idx)

    # 2. Extract Features (X) and Targets (Y)
    # We want one row per sample in the CSV
    # X columns: All unique reagents found
    # Y columns: All groups found (Sour, Sweet, etc.)
    
    data_rows = df_raw.iloc[2:].copy()
    data_rows.reset_index(drop=True, inplace=True)
    
    X_dict = {i: {} for i in data_rows.index}
    Y_dict = {i: {} for i in data_rows.index}
    
    all_feature_names = set()
    
    for group, info in blocks.items():
        indices = info['indices']
        
        # Identify which column in this block is 'Taste' and which are 'Reagents'
        taste_idx = None
        reagent_indices = []
        
        for i in indices:
            header = str(names_row[i]).strip()
            if 'taste' in header.lower():
                taste_idx = i
            elif 'reagent' in header.lower() or 'r' in header.lower(): # Basic heuristic
                reagent_indices.append(i)
                all_feature_names.add(header)
        
        # Extract Y (Target) for this group
        if taste_idx is not None:
            col_data = df_raw.iloc[2:, taste_idx]
            # Convert to numeric, handle 0.5, 1, 0
            # non-numeric becomes 0
            col_data = pd.to_numeric(col_data, errors='coerce').fillna(0)
            
            for row_idx, val in col_data.items():
                # row_idx in df_raw starts at 2. 
                # Our X_dict keys start at 0 (mapped from reset_index)
                # So we map back: row_idx - 2
                internal_idx = row_idx - 2
                if internal_idx in Y_dict:
                    Y_dict[internal_idx][group] = float(val)

        # Extract X (Features) for this group
        for r_idx in reagent_indices:
            feature_name = str(names_row[r_idx]).strip()
            col_data = df_raw.iloc[2:, r_idx]
            col_data = pd.to_numeric(col_data, errors='coerce').fillna(0)
            
            for row_idx, val in col_data.items():
                internal_idx = row_idx - 2
                if internal_idx in X_dict:
                    X_dict[internal_idx][feature_name] = float(val)
                    
    # Convert to DataFrames
    X = pd.DataFrame.from_dict(X_dict, orient='index')
    y = pd.DataFrame.from_dict(Y_dict, orient='index')
    
    # Clean up X
    X = X.fillna(0)
    # Ensure specific column order if possible, or just sort
    # We want consistent column order for the model
    # Reagent 1, Reagent 2...
    # Simple sort works usually
    sorted_features = sorted(list(X.columns), key=lambda x: x.lower())
    X = X[sorted_features]
    
    # Clean up y
    y = y.fillna(0) # If a group was missing for a row, assume 0 intensity
    
    print(f"Processed Multi-Output Data: {len(X)} samples.")
    print(f"Input Features ({len(X.columns)}): {list(X.columns)}")
    print(f"Target Tastes ({len(y.columns)}): {list(y.columns)}")
    
    return X, y, list(X.columns)

def load_csv_data(filepath):
    print(f"Loading CSV from {filepath}...")
    df = pd.read_csv(filepath)
    return process_flat_df(df)

def load_excel_flat(filepath):
    print(f"Loading Flat Excel from {filepath}...")
    df = pd.read_excel(filepath)
    return process_flat_df(df)

def process_flat_df(df):
    # Normalize columns
    # Look for target column
    target_col = None
    cols_lower = {c: c.lower().strip() for c in df.columns}
    
    for original, lower in cols_lower.items():
        if lower in ['taste', 'class', 'label']:
            target_col = original
            break
            
    if not target_col:
        raise ValueError("Could not find 'taste' column in CSV.")
        
    y = df[target_col]
    X = df.drop(columns=[target_col])
    
    # 1. Drop known metadata/leak columns
    ignore_keywords = ['sr. no', 'sour', 'astringent', 'bitter', 'salty', 'sweet', 'pungent']
    to_drop = []
    for col in X.columns:
        c_low = col.lower().strip()
        if any(k in c_low for k in ignore_keywords):
            to_drop.append(col)
            
    if to_drop:
        print(f"Dropping non-feature columns: {to_drop}")
        X = X.drop(columns=to_drop)
        
    # 2. Drop completely empty columns
    X = X.dropna(axis=1, how='all')
    
    # 3. Fill remaining NaNs with 0
    X = X.fillna(0)
        
    return X, y, list(X.columns)

if __name__ == "__main__":
    # Test
    try:
        X, y, cols = load_data("mock_taste_data.xlsx")
        print("Data Loaded Successfully.")
        print("Features:", cols)
        print("Target Counts:\n", y.value_counts())
        print("Shape:", X.shape)
    except Exception as e:
        print(f"Error: {e}")
