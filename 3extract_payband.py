#!/usr/bin/env python3
import pandas as pd
import numpy as np
import re

# Read the Excel file
file_path = "/Users/anaavendano/Documents/TMRL/HR Comp Data & HC __ People Analytics Exercise.xlsx"
paybands = pd.read_excel(file_path, sheet_name='Paybands')

print("=== EXTRACTING ROLES FROM PAYBANDS ===")

# The role names are actually in the DataFrame column names, not in row 1
# Let's extract them properly
role_columns = []
for i, col_name in enumerate(paybands.columns):
    if not str(col_name).startswith('Unnamed'):
        role_columns.append((i, str(col_name)))
        print(f"Column {i}: {col_name}")

print(f"\nFound {len(role_columns)} role categories")

# Now let's map the Early/Seasoned/Veteran groups to these roles
# Find all Early/Seasoned/Veteran column groups
esv_groups = []
for col_idx in range(len(paybands.columns) - 2):
    val1 = str(paybands.iloc[1, col_idx]).strip()
    val2 = str(paybands.iloc[1, col_idx + 1]).strip()  
    val3 = str(paybands.iloc[1, col_idx + 2]).strip()
    
    if val1 == 'Early' and val2 == 'Seasoned' and val3 == 'Veteran':
        esv_groups.append(col_idx)

print(f"\nFound Early/Seasoned/Veteran groups at columns: {esv_groups}")

# Map each ESV group to the corresponding role
# Based on the pattern, each role should have one ESV group
role_assignments = []
for i, (role_col, role_name) in enumerate(role_columns):
    if i < len(esv_groups):
        esv_col = esv_groups[i]
        role_assignments.append({
            'role_name': role_name,
            'role_column': role_col,
            'early_col': esv_col,
            'seasoned_col': esv_col + 1,
            'veteran_col': esv_col + 2
        })
        print(f"Role '{role_name}' -> ESV columns {esv_col}-{esv_col+2}")

# Process the data with correct role mappings
structured_data = []
comp_id = 1

seniority_mapping = {
    'Early': 1,
    'Seasoned': 2,
    'Veteran': 3
}

for role_assignment in role_assignments:
    role_name = role_assignment['role_name']
    print(f"\nProcessing role: {role_name}")
    
    # Process level data starting from row 2
    row_idx = 2
    while row_idx < len(paybands) - 3:
        # Look for level indicators
        level_found = False
        level_code = None
        level_id = None
        
        for check_col in range(min(5, len(paybands.columns))):
            cell_val = str(paybands.iloc[row_idx, check_col]).strip()
            if re.match(r'^(L\d+|M\d+)$', cell_val):
                level_code = cell_val
                level_id = int(re.search(r'(\d+)', level_code).group(1))
                level_found = True
                break
        
        if not level_found:
            row_idx += 1
            continue
        
        # Check if this is a cash row
        desc_cell = str(paybands.iloc[row_idx, 1]).strip().lower()
        if 'cash' not in desc_cell:
            row_idx += 1
            continue
        
        print(f"  Processing {level_code}")
        
        try:
            # Extract data for each seniority level
            for seniority_name in ['Early', 'Seasoned', 'Veteran']:
                seniority_col = role_assignment[f'{seniority_name.lower()}_col']
                
                # Extract all 4 values
                cash_base = paybands.iloc[row_idx, seniority_col]
                equity_value = paybands.iloc[row_idx + 1, seniority_col]
                equity_units = paybands.iloc[row_idx + 2, seniority_col]
                annual_total = paybands.iloc[row_idx + 3, seniority_col]
                
                # Clean numeric values
                def clean_numeric(val):
                    if pd.isna(val):
                        return 0
                    try:
                        return int(float(str(val).replace(',', '').replace('$', '')))
                    except:
                        return 0
                
                cash_base = clean_numeric(cash_base)
                equity_value = clean_numeric(equity_value)
                equity_units = clean_numeric(equity_units)
                annual_total = clean_numeric(annual_total)
                
                # Only add if we have meaningful data
                if cash_base > 0 or equity_value > 0 or annual_total > 0:
                    structured_data.append({
                        'comp_id': comp_id,
                        'role_category': role_name,
                        'level_id': level_id,
                        'level_code': level_code,
                        'seniority_id': seniority_mapping[seniority_name],
                        'seniority_name': seniority_name,
                        'cash_base': cash_base,
                        'equity_value': equity_value,
                        'equity_units': equity_units,
                        'annual_total': annual_total
                    })
                    
                    print(f"    {seniority_name}: Cash=${cash_base:,}")
                    comp_id += 1
            
            # Move to next level
            row_idx += 4
            
        except IndexError:
            break
        except Exception as e:
            print(f"    Error: {e}")
            row_idx += 1

# Create final dataset
if structured_data:
    final_df = pd.DataFrame(structured_data)
    
    print(f"\n" + "="*60)
    print("FINAL PAYBAND DATABASE WITH ROLES")
    print("="*60)
    print(f"Total records: {len(final_df)}")
    print(f"Unique roles: {final_df['role_category'].nunique()}")
    
    print(f"\nRole distribution:")
    role_counts = final_df['role_category'].value_counts()
    for role, count in role_counts.items():
        print(f"  {role}: {count} records")
    
    # Save complete data with all details
    final_df.to_csv('payband_database_complete.csv', index=False)
    
    print(f"\n✅ FINAL FILE CREATED:")
    print(f"  - payband_database_complete.csv: Complete payband database with role names and details")
    
    # Show sample of complete database
    print(f"\n🎯 SAMPLE OF PAYBAND DATABASE:")
    sample_data = final_df[['comp_id', 'role_category', 'level_code', 'seniority_name', 'cash_base', 'annual_total']].head(10)
    print(sample_data)

else:
    print("❌ No data extracted")

print("\nDatabase creation complete!")