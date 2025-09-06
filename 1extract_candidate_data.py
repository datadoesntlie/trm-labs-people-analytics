#!/usr/bin/env python3
import pandas as pd

# Read the Excel file
file_path = "/Users/anaavendano/Documents/TMRL/HR Comp Data & HC __ People Analytics Exercise.xlsx"

print("=== EXTRACTING CANDIDATE COMP DATA FROM 2025 ===")

# Read the Candidate Comp Data sheet
candidate_data = pd.read_excel(file_path, sheet_name='Candidate Comp Data from 2025')

print(f"Loaded {len(candidate_data)} candidate records with {len(candidate_data.columns)} columns")

# Show basic info about the data
print(f"\nColumns in the dataset:")
for i, col in enumerate(candidate_data.columns, 1):
    print(f"{i:2d}. {col}")

# Save to CSV
output_file = 'candidate_comp_data_2025.csv'
candidate_data.to_csv(output_file, index=False)

print(f"\n✅ Candidate Comp Data exported to: {output_file}")
print(f"📊 Dataset contains {len(candidate_data)} records")

# Show first few rows as preview
print(f"\nPreview of first 5 records:")
print(candidate_data.head())

print(f"\nExtraction complete!")