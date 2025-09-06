#!/usr/bin/env python3
"""
TRM Labs Data Extraction Script
===============================

Combined script that extracts all data from Excel file:
1. Candidate composition data
2. Geographic adjustment factors  
3. Payband database

Portable script that works in any environment without hardcoded paths.

Usage:
    python extract_all_data.py

Author: Ana Avendano
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_section(message):
    """Print a section header"""
    print(f"\n{message}")
    print("-" * 60)

def get_excel_file_path():
    """
    Get the Excel file path using relative path from script directory
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_filename = "HR Comp Data & HC __ People Analytics Exercise.xlsx"
    file_path = os.path.join(script_dir, excel_filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    return file_path

def extract_candidate_data(file_path):
    """Extract candidate composition data"""
    print_section("=== EXTRACTING CANDIDATE COMP DATA FROM 2025 ===")
    
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
    
    print(f"\nCandidate data extraction complete!")
    return True

def extract_geofactors_data(file_path):
    """Extract geographic factors data"""
    print_section("=== EXTRACTING GEOFACTORS DATA ===")
    
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
    
    print(f"\nGeoFactors data extraction complete!")
    return True

def extract_payband_data(file_path):
    """Extract payband database"""
    print_section("=== EXTRACTING ROLES FROM PAYBANDS ===")
    
    paybands = pd.read_excel(file_path, sheet_name='Paybands')
    
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
        
        print("\nPayband database creation complete!")
        return True
    else:
        print("❌ No payband data extracted")
        return False

def main():
    """Main extraction function"""
    start_time = datetime.now()
    
    print_banner("TRM LABS COMBINED DATA EXTRACTION")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get the Excel file path
        file_path = get_excel_file_path()
        print(f"\nUsing Excel file: {os.path.basename(file_path)}")
        
        # Track success/failure of each extraction
        results = {
            'candidate_data': False,
            'geofactors_data': False, 
            'payband_data': False
        }
        
        # Extract candidate data
        try:
            results['candidate_data'] = extract_candidate_data(file_path)
        except Exception as e:
            print(f"❌ Error extracting candidate data: {str(e)}")
        
        # Extract geofactors data
        try:
            results['geofactors_data'] = extract_geofactors_data(file_path)
        except Exception as e:
            print(f"❌ Error extracting geofactors data: {str(e)}")
        
        # Extract payband data
        try:
            results['payband_data'] = extract_payband_data(file_path)
        except Exception as e:
            print(f"❌ Error extracting payband data: {str(e)}")
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_banner("EXTRACTION SUMMARY")
        print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        
        successful_extractions = sum(results.values())
        total_extractions = len(results)
        
        print(f"\nExtractions completed: {successful_extractions}/{total_extractions}")
        
        for data_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {data_type}: {status}")
        
        if successful_extractions == total_extractions:
            print("\n🎉 All extractions completed successfully!")
            
            # List output files
            output_files = [
                "candidate_comp_data_2025.csv",
                "geofactors_data.csv", 
                "payband_database_complete.csv"
            ]
            
            print("\n📁 Generated files:")
            for file in output_files:
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    print(f"   ✅ {file} ({size:,} bytes)")
                else:
                    print(f"   ❓ {file} (not found)")
            
            print("\n🔗 Repository: https://github.com/datadoesntlie/trm-labs-people-analytics")
            print("\nCombined extraction complete! 🚀")
        else:
            failed_count = total_extractions - successful_extractions
            print(f"\n⚠️  Extraction completed with {failed_count} failure(s).")
            print("Please check the output above for details on failed extractions.")
            return 1
            
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ {str(e)}")
        print("Make sure the Excel file 'HR Comp Data & HC __ People Analytics Exercise.xlsx' exists in the same directory as this script.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Change to script directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction interrupted by user.")
        print("Partial results may be available.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error in extraction: {str(e)}")
        exit(1)