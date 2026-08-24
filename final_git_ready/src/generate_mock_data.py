
import pandas as pd
import numpy as np

def generate_mock_excel(filename="mock_taste_data.xlsx"):
    # Create a structure mimicking the user's image
    # Row 0: Taste Categories (spanning multiple columns)
    # Row 1: Reagent Names
    # Row 2+: Data

    # We'll construct this using a MultiIndex concept or just raw cell insertion.
    
    # Define Tastes and their corresponding Reagents
    # STRICTLY ALIGNING with the 10 Sensors available in the App
    structure = {
        "Sour": ["reagent 1 (mo)", "reagent 2", "reagent 3"],
        "Astringent": ["reagent 4", "reagent 5", "reagent 6"], 
        "Sweet": ["reagent 1 (mo)", "reagent 5", "reagent 6"],
        "Bitter": ["reagent 2", "reagent 7"],
        "Salty": ["reagent 8", "reagent 9"],
        "Pungent": ["reagent 10"]
    }

    # Number of samples per taste
    n_samples = 20

    data_rows = []
    
    flat_columns = []
    header_row_0 = [] # Taste
    header_row_1 = [] # Reagents

    for taste, reagents in structure.items():
        # For the header row 0, we put the Taste name in the first column of the group
        header_row_0.append(taste)
        # Empty cells for the rest of this group (reagents + 1 for the Taste col)
        header_row_0.extend([np.nan] * len(reagents))
        
        # Header row 1 is "Taste" then reagents
        header_row_1.append("Taste Label") # Using "Taste Label" to match data_loader search for "taste"
        header_row_1.extend(reagents)
        
        # Keep track for data generation
        flat_columns.append((taste, "Taste Label"))
        flat_columns.extend([(taste, r) for r in reagents])

    # Now generate random data
    # The image implies 'Sr. No.' is the first column.
    
    final_header_0 = [""] + header_row_0
    final_header_1 = ["Sr. No."] + header_row_1

    # Create dataframe for the data part
    data = []
    
    # Taste Keys
    tastes_list = list(structure.keys())

    for i in range(1, n_samples + 1):
        row = [i]
        
        # 1. Pick an active taste for this sample
        # Occasionally make a "Complex" sample (two tastes), but mostly pure.
        if np.random.random() < 0.8:
            active_tastes = [np.random.choice(tastes_list)]
        else:
            active_tastes = np.random.choice(tastes_list, 2, replace=False)
            
        # 2. Identify Active Reagents for this row
        active_reagents = set()
        for t in active_tastes:
            for r in structure[t]:
                active_reagents.add(r)
                
        # 3. Fill Columns
        for taste_group, col_name in flat_columns:
            if col_name == "Taste Label":
                # Target Column
                if taste_group in active_tastes:
                    row.append(1.0)
                else:
                    row.append(0.0)
            else:
                # Reagent Column
                # Check if this reagent should be active
                # Note: col_name is "reagent 1 (mo)" etc.
                if col_name in active_reagents:
                     # High Signal
                     row.append(np.random.uniform(150, 250))
                else:
                     # Low Signal / Noise
                     row.append(np.random.uniform(0, 60))
            
        data.append(row)

    # Create DataFrame
    df = pd.DataFrame(data, columns=final_header_1)
    
    # We need to construct the complicated multi-header manually or save specifically.
    # Pandas MultiIndex is best.
    
    # Create MultiIndex Columns
    # Level 0: Taste
    # Level 1: Reagent
    
    tuples = []
    # Sr No
    tuples.append(("metadata", "Sr. No."))
    
    for taste, reagents in structure.items():
        tuples.append((taste, "Taste Label"))
        for r in reagents:
            tuples.append((taste, r))
            
    columns = pd.MultiIndex.from_tuples(tuples, names=["Taste", "Reagent"])
    
    # Re-create DF with proper index
    df_multi = pd.DataFrame(data, columns=columns)
    
    # Save to Excel
    # We want it to look like the image: Merged cells for Taste at top.
    # Writing MultiIndex columns with index=False is not supported in some versions.
    # We will write with index=True, but we can set the index to be the "Sr. No." first.
    
    # Or simply:
    try:
        df_multi.to_excel(filename, index=True)
    except Exception:
        # Fallback: Flatten columns if multindex fails
        df_multi.columns = ['_'.join(col).strip() for col in df_multi.columns.values]
        df_multi.to_excel(filename, index=False)

    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_mock_excel()
