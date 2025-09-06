#!/usr/bin/env python3
import pandas as pd

# Read the Excel file
file_path = "/Users/anaavendano/Documents/TMRL/HR Comp Data & HC __ People Analytics Exercise.xlsx"

print("=== EXTRACTING GEOFACTORS DATA ===")

# Read the GeoFactors sheet
geofactors_data = pd.read_excel(file_path, sheet_name='GeoFactors')

print(f"Loaded {len(geofactors_data)} records with {len(geofactors_data.columns)} columns")

# Show basic info about the data
print(f"\nColumns in the dataset:")
for i, col in enumerate(geofactors_data.columns, 1):
    print(f"{i:2d}. {col}")

# Save to CSV
output_file = 'geofactors_data.csv'
geofactors_data.to_csv(output_file, index=False)

print(f"\n✅ GeoFactors data exported to: {output_file}")
print(f"📊 Dataset contains {len(geofactors_data)} records")

# Show first few rows as preview
print(f"\nPreview of first 10 records:")
print(geofactors_data.head(10))

# Show data types
print(f"\nData types:")
print(geofactors_data.dtypes)

print(f"\nExtraction complete!")