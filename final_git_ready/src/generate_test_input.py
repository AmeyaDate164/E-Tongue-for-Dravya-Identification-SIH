
import pandas as pd
import numpy as np

# Define the features exactly as in generate_mock_data
columns = [
    "reagent 1 (mo)", "reagent 2", "reagent 3", # Sour
    "reagent 4", "G2", "B2", "R3", "G3", "B3", "R4", "G4", # Astringent
    "reagent 5", "reagent 6", # Sweet
    "reagent 7", # Bitter
    "reagent 8", "reagent 9", # Salty
    "reagent 10" # Pungent
]

# Create 2 samples
# Sample 1: Sour heavy
data1 = {c: 10.0 for c in columns} # Baseline
data1["reagent 1 (mo)"] = 100.0
data1["reagent 2"] = 100.0

# Sample 2: Sweet heavy
data2 = {c: 10.0 for c in columns}
data2["reagent 5"] = 120.0
data2["reagent 6"] = 130.0

# Sample 3: Salty
data3 = {c: 10.0 for c in columns}
data3["reagent 8"] = 150.0

# Sample 4: Perfect Sour (Extreme High Confidence)
data4 = {c: 0.0 for c in columns}
data4["reagent 1 (mo)"] = 500.0
data4["reagent 2"] = 500.0
data4["reagent 3"] = 500.0 

df = pd.DataFrame([data1, data2, data3, data4])

# Sample 5: The "Complex Mix" (>3 Tastes)
# We will trigger Astringent, Sweet, Salty, and Pungent simultaneously.
data5 = {c: 10.0 for c in columns}
data5["reagent 4"] = 150.0  # Astringent
data5["reagent 5"] = 140.0  # Sweet
data5["reagent 8"] = 160.0  # Salty
data5["reagent 10"] = 150.0 # Pungent

df = pd.DataFrame([data1, data2, data3, data4, data5])

df.to_csv("test_input.csv", index=False)
print("Created test_input.csv")
