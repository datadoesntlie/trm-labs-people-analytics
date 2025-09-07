#!/usr/bin/env python3
import pandas as pd
import numpy as np
import re
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Read the Excel file using relative path
file_path = os.path.join(script_dir, "HR Comp Data & HC __ People Analytics Exercise.xlsx")
paybands = pd.read_excel(file_path, sheet_name='Paybands')

print("=== EXTRACTING ROLES FROM PAYBANDS ===")

def detect_payband_blocks(df):
    """
    Detect payband blocks by finding empty column separators
    Returns list of (start_col, end_col, role_name) tuples
    """
    blocks = []
    
    # Find role names in header row (non-unnamed columns)
    role_columns = []
    for i, col_name in enumerate(df.columns):
        if not str(col_name).startswith('Unnamed'):
            role_columns.append((i, str(col_name)))
    
    print(f"Found {len(role_columns)} role categories:")
    for col_idx, role_name in role_columns:
        print(f"  Column {col_idx}: {role_name}")
    
    # Each role should have a ~5-column payband block
    # Look for patterns: role_col, empty, data_col1, data_col2, data_col3, empty, next_role...
    for i, (role_col, role_name) in enumerate(role_columns):
        # Payband data typically starts 2 columns after the role name
        start_col = role_col + 2
        
        # Find the end by looking for the next role or end of sheet
        if i + 1 < len(role_columns):
            next_role_col = role_columns[i + 1][0]
            end_col = next_role_col  # Up to but not including next role
        else:
            end_col = len(df.columns)  # Last block goes to end
        
        blocks.append((start_col, end_col, role_name, role_col))
        print(f"  Block: {role_name} -> columns {start_col} to {end_col-1}")
    
    return blocks

def stack_payband_blocks(df, blocks):
    """
    Stack all payband blocks into a unified 5-column format
    """
    stacked_data = []
    
    for start_col, end_col, role_name, role_col in blocks:
        print(f"\nProcessing block: {role_name}")
        
        # Extract this block's data (typically 3-4 columns: Early, Seasoned, Veteran + maybe one more)
        block_width = end_col - start_col
        
        # Create a copy of the dataframe with just this block's columns
        block_data = pd.DataFrame()
        
        # Map this block to standard 5-column format
        # Column 0: Role indicator (we'll add the role name)
        # Column 1: Level/description 
        # Columns 2-4: Early, Seasoned, Veteran data
        
        for row_idx in range(len(df)):
            row_data = []
            
            # Column 0: Role name
            row_data.append(role_name)
            
            # Column 1: Get description/level from the role column or adjacent
            desc_val = str(df.iloc[row_idx, role_col]).strip()
            if desc_val == 'nan' or desc_val == '' or 'Unnamed' in desc_val:
                # Try the column right before the data starts
                if start_col > 0:
                    desc_val = str(df.iloc[row_idx, start_col - 1]).strip()
            row_data.append(desc_val)
            
            # Columns 2-4: Data columns (Early, Seasoned, Veteran)
            for col_offset in range(3):  # Assume 3 seniority columns
                if start_col + col_offset < end_col:
                    val = df.iloc[row_idx, start_col + col_offset]
                    row_data.append(val)
                else:
                    row_data.append(np.nan)
            
            # Add any additional columns as needed
            while len(row_data) < 5:
                row_data.append(np.nan)
            
            stacked_data.append(row_data)
    
    # Create stacked DataFrame
    stacked_df = pd.DataFrame(stacked_data, columns=['Role', 'Description', 'Early', 'Seasoned', 'Veteran'])
    
    print(f"\nStacked data shape: {stacked_df.shape}")
    print("Sample of stacked data:")
    print(stacked_df.head(10))
    
    return stacked_df

# Detect and stack payband blocks
blocks = detect_payband_blocks(paybands)
stacked_paybands = stack_payband_blocks(paybands, blocks)

# Now use the stacked data for processing
paybands = stacked_paybands

# Update role_columns to match new format
role_columns = []
unique_roles = paybands['Role'].unique()
for i, role_name in enumerate(unique_roles):
    if not pd.isna(role_name) and str(role_name) != 'nan':
        role_columns.append((0, str(role_name)))  # All roles are now in column 0

print(f"\nFound {len(role_columns)} role categories")

# In the stacked format, Early/Seasoned/Veteran are in columns 2, 3, 4
# Create role assignments for the stacked format
role_assignments = []
for role_col, role_name in role_columns:
    role_assignments.append({
        'role_name': role_name,
        'role_column': 0,  # Role is always in column 0 now
        'early_col': 2,    # Early data in column 2
        'seasoned_col': 3, # Seasoned data in column 3
        'veteran_col': 4   # Veteran data in column 4
    })
    print(f"Role '{role_name}' -> ESV columns 2-4")

# Process the data with correct role mappings
structured_data = []
comp_id = 1

seniority_mapping = {
    'Early': 1,
    'Seasoned': 2,
    'Veteran': 3
}

# Process the stacked data
for role_assignment in role_assignments:
    role_name = role_assignment['role_name']
    print(f"\nProcessing role: {role_name}")
    
    # Filter rows for this specific role
    role_data = paybands[paybands['Role'] == role_name].copy().reset_index(drop=True)
    
    if len(role_data) == 0:
        print(f"  No data found for {role_name}")
        continue
    
    # Process each row to find level indicators and cash data
    row_idx = 0
    while row_idx < len(role_data) - 3:
        # Look for level indicators in the Description column
        desc_val = str(role_data.iloc[row_idx, 1]).strip()  # Column 1 is Description
        level_code = None
        level_id = None
        
        # Check if this row contains a level code (L1, L2, M3, etc.)
        if re.match(r'^(L\d+|M\d+)$', desc_val):
            level_code = desc_val
            level_id = int(re.search(r'(\d+)', level_code).group(1))
            # For the stacked format, the cash data is right in this row
            cash_row_idx = row_idx
        else:
            row_idx += 1
            continue
        
        print(f"  Processing {level_code}")
        
        try:
            # Extract data for each seniority level from the cash row
            for seniority_name in ['Early', 'Seasoned', 'Veteran']:
                seniority_col = role_assignment[f'{seniority_name.lower()}_col']
                
                # Extract all 4 values starting from cash row
                if cash_row_idx + 3 < len(role_data):
                    cash_base = role_data.iloc[cash_row_idx, seniority_col]
                    equity_value = role_data.iloc[cash_row_idx + 1, seniority_col]
                    equity_units = role_data.iloc[cash_row_idx + 2, seniority_col]
                    annual_total = role_data.iloc[cash_row_idx + 3, seniority_col]
                else:
                    # Not enough rows for full data
                    continue
                
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
            
            # Move to next level (skip the 4 rows we just processed)
            row_idx = cash_row_idx + 4
            
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