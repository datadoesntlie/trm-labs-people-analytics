#!/usr/bin/env python3
"""
Candidate Composition Data 2025 Cleaning Script

This script performs the following cleaning operations:
1. Adds 'Candidate Number' column by extracting numbers from 'Candidate Name + GH URL'
2. Fills missing Date values using linear interpolation based on candidate number order
3. Filters out incomplete records (missing Location/Unknown, High Potential?, Geo Factor, Comp Type, Current Level, $ Base Comp) to separate file
4. Updates Geo Factor values based on location and tech/non-tech role type using geofactors_data.csv
5. Adds 'Compensation Difference' column (TRM Cash - $ Base Comp)
6. Updates TRM Cash values based on payband database (Final Pay Band × Current Level × Geo Factor)
7. Adds 'TRM Level Cash' column based on payband database (Final Pay Band × TRM Level × Geo Factor)

Usage:
    python clean_candidate_composition_2025.py
"""

import pandas as pd
import numpy as np
import re

def load_geo_factors(geo_file='geofactors_data.csv'):
    """
    Load and prepare geo factors lookup table including averages for Unknown locations
    
    Args:
        geo_file (str): Path to geo factors CSV file
    
    Returns:
        dict: Geo factors lookup dictionary with averages for Unknown location
    """
    geo_df = pd.read_csv(geo_file)
    
    # Clean column names
    geo_df.columns = geo_df.columns.str.strip()
    
    # Calculate averages for Unknown location
    non_tech_avg = geo_df['Geo Factor for non tech roles'].mean()
    tech_avg = geo_df['Geo Factor for tech roles (Including Solutions Engineering, but excluding P. I.)'].mean()
    
    # Create lookup dictionary for easier access
    geo_lookup = {}
    for _, row in geo_df.iterrows():
        country = row['Country']
        if pd.notna(country):
            geo_lookup[country] = {
                'non_tech': row['Geo Factor for non tech roles'],
                'tech': row['Geo Factor for tech roles (Including Solutions Engineering, but excluding P. I.)'],
                'us_or_non_us': row['Us or Non US']
            }
    
    # Add Unknown location with calculated averages
    geo_lookup['Unknown'] = {
        'non_tech': round(non_tech_avg, 3),
        'tech': round(tech_avg, 3),
        'us_or_non_us': 'Unknown'
    }
    
    return geo_lookup, non_tech_avg, tech_avg

def load_payband_database(payband_file='payband_database_complete.csv'):
    """
    Load payband database for TRM Cash validation
    
    Args:
        payband_file (str): Path to payband database CSV file
    
    Returns:
        pd.DataFrame: Payband database for lookups
    """
    payband_df = pd.read_csv(payband_file)
    
    # Create lookup for Seasoned seniority cash_base values
    seasoned_payband = payband_df[payband_df['seniority_name'] == 'Seasoned'].copy()
    
    return seasoned_payband

def extract_level_code(current_level):
    """
    Extract first 2 characters from Current Level field
    
    Args:
        current_level (str): Current Level value like 'L4 (Senior)', 'M4 (Manager)'
    
    Returns:
        str: Level code like 'L4', 'M4'
    """
    if pd.isna(current_level):
        return None
    return str(current_level).strip()[:2]

def update_trm_cash(df, payband_df):
    """
    Update TRM Cash values based on payband database using Final Pay Band
    TRM Cash = Payband cash_base × Geo Factor
    
    Args:
        df (pd.DataFrame): Candidate dataframe
        payband_df (pd.DataFrame): Payband database (Seasoned seniority only)
    
    Returns:
        tuple: (updated_count, calculated_count, no_payband_match_count)
    """
    updated_count = 0
    calculated_count = 0
    no_payband_match_count = 0
    
    for idx, row in df.iterrows():
        final_pay_band = row['Final Pay Band']
        current_level = row['Current Level']
        geo_factor = row['Geo Factor']
        
        # Extract level code from current level
        level_code = extract_level_code(current_level)
        
        if pd.notna(final_pay_band) and pd.notna(level_code) and pd.notna(geo_factor):
            # Try to find matching record in payband
            matching_payband = payband_df[
                (payband_df['role_category'] == final_pay_band) & 
                (payband_df['level_code'] == level_code)
            ]
            
            if not matching_payband.empty:
                base_cash = matching_payband['cash_base'].iloc[0]
                # Calculate TRM Cash using geo factor
                calculated_trm_cash = base_cash * geo_factor
                
                # Get current TRM Cash value
                current_trm_cash = row['TRM Cash']
                
                # Update TRM Cash value (whether it's missing, incorrect, or correct)
                df.at[idx, 'TRM Cash'] = calculated_trm_cash
                calculated_count += 1
                
                # Check if we actually changed the value
                if pd.isna(current_trm_cash) or abs(current_trm_cash - calculated_trm_cash) >= 0.01:
                    updated_count += 1
            else:
                no_payband_match_count += 1
    
    return updated_count, calculated_count, no_payband_match_count

def calculate_trm_level_cash(df, payband_df):
    """
    Calculate TRM Cash using TRM Level instead of Current Level
    TRM Level Cash = Payband cash_base (based on TRM Level) × Geo Factor
    
    Args:
        df (pd.DataFrame): Candidate dataframe
        payband_df (pd.DataFrame): Payband database (Seasoned seniority only)
    
    Returns:
        tuple: (calculated_count, no_payband_match_count)
    """
    calculated_count = 0
    no_payband_match_count = 0
    
    # Initialize new column
    df['TRM Level Cash'] = np.nan
    
    for idx, row in df.iterrows():
        final_pay_band = row['Final Pay Band']
        trm_level = row['TRM Level']
        geo_factor = row['Geo Factor']
        
        # Extract level code from TRM level
        trm_level_code = extract_level_code(trm_level)
        
        if pd.notna(final_pay_band) and pd.notna(trm_level_code) and pd.notna(geo_factor):
            # Try to find matching record in payband using TRM Level
            matching_payband = payband_df[
                (payband_df['role_category'] == final_pay_band) & 
                (payband_df['level_code'] == trm_level_code)
            ]
            
            if not matching_payband.empty:
                base_cash = matching_payband['cash_base'].iloc[0]
                # Calculate TRM Level Cash using geo factor
                trm_level_cash = base_cash * geo_factor
                
                # Set the calculated value
                df.at[idx, 'TRM Level Cash'] = trm_level_cash
                calculated_count += 1
            else:
                no_payband_match_count += 1
    
    return calculated_count, no_payband_match_count

def filter_incomplete_records(df, incomplete_file='incomplete_candidate_records.csv'):
    """
    Filter out records with blank/unknown values in critical fields and save to separate file
    
    Fields checked for blank/unknown values:
    - Location (blank or 'Unknown')
    - High Potential? (blank)
    - Geo Factor (blank)
    - Comp Type (blank)
    - Current Level (blank)
    - $ Base Comp (blank)
    
    Args:
        df (pd.DataFrame): Candidate dataframe
        incomplete_file (str): Path to save incomplete records
    
    Returns:
        tuple: (complete_df, incomplete_df, incomplete_count)
    """
    # Define conditions for incomplete records
    incomplete_mask = (
        df['Location'].isna() |  # Location is blank
        (df['Location'] == 'Unknown') |  # Location is 'Unknown'
        df['High Potential?'].isna() |  # High Potential? is blank
        df['Geo Factor'].isna() |  # Geo Factor is blank
        df['Comp Type'].isna() |  # Comp Type is blank
        df['Current Level'].isna() |  # Current Level is blank
        df['$ Base Comp'].isna()  # $ Base Comp is blank
    )
    
    # Split dataframe
    incomplete_df = df[incomplete_mask].copy()
    complete_df = df[~incomplete_mask].copy()
    
    # Save incomplete records to separate file if any exist
    if len(incomplete_df) > 0:
        incomplete_df.to_csv(incomplete_file, index=False)
        print(f"📋 Saved {len(incomplete_df)} incomplete records to: {incomplete_file}")
    
    return complete_df, incomplete_df, len(incomplete_df)

def update_geo_factors(df, geo_lookup):
    """
    Update Geo Factor column based on location and tech/non-tech role type
    Handle missing locations by setting them to 'Unknown' with appropriate averages
    
    Args:
        df (pd.DataFrame): Candidate dataframe
        geo_lookup (dict): Geo factors lookup dictionary
    
    Returns:
        tuple: (updated_dataframe, updated_count, missing_countries, unknown_location_count)
    """
    updated_count = 0
    missing_countries = set()
    unknown_location_count = 0
    
    for idx, row in df.iterrows():
        location = row['Location']
        role_type = row['Tech/Non-Tech/Quota Carrying']
        
        if pd.isna(location):
            # Set missing location to 'Unknown' and assign average geo factor
            df.at[idx, 'Location'] = 'Unknown'
            unknown_location_count += 1
            location_clean = 'Unknown'
        else:
            location_clean = location.strip()
        
        if pd.notna(role_type):
            if location_clean in geo_lookup:
                # Determine if tech or non-tech
                if role_type.lower().strip() == 'tech':
                    new_geo_factor = geo_lookup[location_clean]['tech']
                else:  # non-tech
                    new_geo_factor = geo_lookup[location_clean]['non_tech']
                
                # Update the geo factor if it's different or missing
                current_geo = df.at[idx, 'Geo Factor']
                if pd.isna(current_geo) or current_geo != new_geo_factor:
                    df.at[idx, 'Geo Factor'] = new_geo_factor
                    updated_count += 1
            else:
                missing_countries.add(location_clean)
    
    return df, updated_count, missing_countries, unknown_location_count

def clean_candidate_data(input_file='candidate_comp_data_2025.csv', output_file='complete_candidate_records.csv', geo_file='geofactors_data.csv'):
    """
    Clean candidate composition data by:
    1. Adding 'Candidate Number' column extracted from 'Candidate Name + GH URL'
    2. Filling missing Date values using linear interpolation based on candidate number order
    3. Filtering out incomplete records (saves to 'incomplete_candidate_records.csv')
    4. Updating Geo Factor values based on location and tech/non-tech role type
    5. Adding 'Compensation Difference' column (TRM Cash - $ Base Comp)
    6. Updating TRM Cash values based on payband database (Final Pay Band × Current Level × Geo Factor)
    7. Adding 'TRM Level Cash' column based on payband database (Final Pay Band × TRM Level × Geo Factor)
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output cleaned CSV file
        geo_file (str): Path to geo factors CSV file
    
    Returns:
        pd.DataFrame: Cleaned dataframe (complete records only)
    """
    
    print("=== CANDIDATE COMPOSITION DATA CLEANING ===")
    
    # Load the data
    df = pd.read_csv(input_file)
    print(f"Loaded data: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Load geo factors lookup table
    print("Loading geo factors data...")
    geo_lookup, non_tech_avg, tech_avg = load_geo_factors(geo_file)
    print(f"✅ Loaded geo factors for {len(geo_lookup)-1} countries")
    print(f"📊 Calculated averages - Non-tech: {non_tech_avg:.3f}, Tech: {tech_avg:.3f}")
    
    # Load payband database for TRM Cash validation
    print("Loading payband database...")
    payband_df = load_payband_database()
    print(f"✅ Loaded {len(payband_df)} payband records for validation")
    
    # Step 1: Add Candidate Number column
    def extract_candidate_number(name):
        """Extract candidate number from name string like 'Candidate 1' -> 1"""
        if pd.isna(name):
            return None
        match = re.search(r'Candidate\s+(\d+)', str(name))
        return int(match.group(1)) if match else None
    
    df['Candidate Number'] = df['Candidate Name + GH URL'].apply(extract_candidate_number)
    print(f"✅ Added Candidate Number column")
    print(f"   Candidate numbers range: {df['Candidate Number'].min()} to {df['Candidate Number'].max()}")
    
    # Step 2: Sort by Candidate Number for proper interpolation order
    df_sorted = df.sort_values('Candidate Number').reset_index(drop=True)
    
    # Check for missing dates before interpolation
    original_missing = df_sorted['Date'].isna().sum()
    print(f"📊 Missing date values before interpolation: {original_missing}")
    
    # Step 3: Linear interpolation of missing dates
    # Convert Date column to datetime for interpolation
    df_sorted['Date'] = pd.to_datetime(df_sorted['Date'], errors='coerce')
    
    # Perform linear interpolation based on candidate number order
    df_sorted['Date'] = df_sorted['Date'].interpolate(method='linear')
    
    # Convert dates back to string format to match original
    df_sorted['Date'] = df_sorted['Date'].dt.strftime('%Y-%m-%d')
    
    print(f"✅ Filled {original_missing} missing date values using linear interpolation")
    
    # Step 4: Filter out incomplete records (save to separate file)
    print("\n🔍 Filtering incomplete records...")
    df_complete, df_incomplete, incomplete_count = filter_incomplete_records(df_sorted)
    
    if incomplete_count > 0:
        print(f"⚠️  {incomplete_count} records filtered out due to missing critical data")
        print("   Critical fields: Location (blank/Unknown), High Potential?, Geo Factor, Comp Type, Current Level, $ Base Comp")
    else:
        print("✅ All records have complete critical data")
    
    # Continue processing with complete records only
    df_sorted = df_complete
    
    # Step 5: Update Geo Factor values based on location and role type
    print("\n🌍 Updating Geo Factor values...")
    df_sorted, updated_count, missing_countries, unknown_location_count = update_geo_factors(df_sorted, geo_lookup)
    print(f"✅ Updated {updated_count} geo factor values")
    
    if missing_countries:
        print(f"⚠️  Countries not found in geo factors data: {sorted(missing_countries)}")
    
    if unknown_location_count > 0:
        print(f"📍 Records set to 'Unknown' location with average geo factors: {unknown_location_count}")
    
    # Step 6: Add Compensation Difference column
    print("\n💰 Calculating Compensation Difference...")
    
    def calculate_compensation_difference(base_comp, trm_cash):
        """
        Calculate compensation difference: TRM Cash - $ Base Comp
        Handle non-numeric values in $ Base Comp
        """
        if pd.isna(base_comp) or pd.isna(trm_cash):
            return np.nan
        
        # Handle string values in base_comp
        if isinstance(base_comp, str):
            base_comp_clean = base_comp.strip()
            # Skip non-numeric entries like 'DNP', 'N/A', etc.
            if base_comp_clean in ['DNP', 'N/A', 'TBD', ''] or not base_comp_clean.replace('.', '').replace('-', '').isdigit():
                return np.nan
            try:
                base_comp_numeric = float(base_comp_clean)
            except ValueError:
                return np.nan
        else:
            base_comp_numeric = float(base_comp)
        
        return trm_cash - base_comp_numeric
    
    df_sorted['Compensation Difference'] = df_sorted.apply(
        lambda row: calculate_compensation_difference(row['$ Base Comp'], row['TRM Cash']), 
        axis=1
    )
    
    # Count successful calculations
    comp_diff_calculated = df_sorted['Compensation Difference'].notna().sum()
    comp_diff_missing = df_sorted['Compensation Difference'].isna().sum()
    
    print(f"✅ Calculated compensation differences for {comp_diff_calculated} records")
    print(f"📊 Unable to calculate for {comp_diff_missing} records (missing or invalid base compensation)")
    
    # Step 7: Update TRM Cash values based on payband database
    print("\n💰 Updating TRM Cash values...")
    updated_count, calculated_count, no_payband_match_count = update_trm_cash(df_sorted, payband_df)
    
    if calculated_count > 0:
        print(f"✅ TRM Cash update completed:")
        print(f"   - {calculated_count} records had TRM Cash calculated from payband")
        print(f"   - {updated_count} records had their TRM Cash value updated")
        print(f"   - {calculated_count - updated_count} records already had correct TRM Cash values")
        
        if no_payband_match_count > 0:
            print(f"   - {no_payband_match_count} records have no matching payband entry (TRM Cash unchanged)")
    else:
        print("⚠️  No TRM Cash values could be calculated (missing role/level data)")
    
    # Step 8: Calculate TRM Level Cash (similar to TRM Cash but using TRM Level)
    print("\n💼 Calculating TRM Level Cash...")
    trm_level_calculated, trm_level_no_match = calculate_trm_level_cash(df_sorted, payband_df)
    
    if trm_level_calculated > 0:
        print(f"✅ TRM Level Cash calculation completed:")
        print(f"   - {trm_level_calculated} records had TRM Level Cash calculated")
        
        if trm_level_no_match > 0:
            print(f"   - {trm_level_no_match} records have no matching payband entry for TRM Level")
    else:
        print("⚠️  No TRM Level Cash values could be calculated (missing TRM Level/payband data)")
    
    # Step 9: Reorder columns to put Candidate Number right after Candidate Name + GH URL
    cols = df_sorted.columns.tolist()
    name_idx = cols.index('Candidate Name + GH URL')
    cols.insert(name_idx + 1, cols.pop(cols.index('Candidate Number')))
    df_final = df_sorted[cols]
    
    # Step 10: Save the cleaned data
    df_final.to_csv(output_file, index=False)
    
    print(f"💾 Cleaned data saved as: {output_file}")
    print(f"📈 Final data: {df_final.shape[0]} rows, {df_final.shape[1]} columns")
    
    # Verify no missing dates remain
    remaining_missing = df_final['Date'].isna().sum()
    print(f"🔍 Missing date values after cleaning: {remaining_missing}")
    
    return df_final

def show_cleaning_summary(df):
    """Display a summary of the cleaned data"""
    print("\n=== CLEANING SUMMARY ===")
    print("Sample of cleaned data:")
    print(df[['Candidate Name + GH URL', 'Candidate Number', 'Date', 'Location', 'Tech/Non-Tech/Quota Carrying', 'Geo Factor', 'TRM Cash', 'TRM Level Cash', 'Compensation Difference']].head(10))
    
    print(f"\nData validation:")
    print(f"- Total records: {len(df)}")
    print(f"- Candidate numbers: {df['Candidate Number'].nunique()} unique values")
    print(f"- Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"- Missing dates: {df['Date'].isna().sum()}")
    print(f"- Missing candidate numbers: {df['Candidate Number'].isna().sum()}")
    print(f"- Missing geo factors: {df['Geo Factor'].isna().sum()}")
    print(f"- Missing TRM Cash: {df['TRM Cash'].isna().sum()}")
    print(f"- Missing TRM Level Cash: {df['TRM Level Cash'].isna().sum()}")
    print(f"- Missing compensation differences: {df['Compensation Difference'].isna().sum()}")
    print(f"- Unique locations: {df['Location'].nunique()}")
    print(f"- Tech vs Non-tech: {df['Tech/Non-Tech/Quota Carrying'].value_counts().to_dict()}")
    
    # Show compensation difference statistics
    if df['Compensation Difference'].notna().sum() > 0:
        comp_diff_stats = df['Compensation Difference'].describe()
        print(f"\\nCompensation Difference Statistics:")
        print(f"- Mean: ${comp_diff_stats['mean']:,.2f}")
        print(f"- Median: ${comp_diff_stats['50%']:,.2f}")
        print(f"- Min: ${comp_diff_stats['min']:,.2f}")
        print(f"- Max: ${comp_diff_stats['max']:,.2f}")
    
    # Show TRM Level Cash vs TRM Cash comparison
    if df['TRM Level Cash'].notna().sum() > 0 and df['TRM Cash'].notna().sum() > 0:
        # Calculate difference between TRM Level Cash and TRM Cash
        cash_diff = df['TRM Level Cash'] - df['TRM Cash']
        cash_diff_stats = cash_diff.describe()
        print(f"\\nTRM Level Cash vs TRM Cash Difference Statistics:")
        print(f"- Mean difference: ${cash_diff_stats['mean']:,.2f}")
        print(f"- Median difference: ${cash_diff_stats['50%']:,.2f}")
        print(f"- Min difference: ${cash_diff_stats['min']:,.2f}")
        print(f"- Max difference: ${cash_diff_stats['max']:,.2f}")
        
        # Count how many are the same vs different
        same_values = (abs(cash_diff) < 0.01).sum()
        different_values = (abs(cash_diff) >= 0.01).sum()
        print(f"- Records with same TRM Cash and TRM Level Cash: {same_values}")
        print(f"- Records with different values: {different_values}")

def create_cleaning_summary_report(df, original_count, filtered_count, summary_file='candidate_cleaning_report.txt'):
    """Create a detailed cleaning summary report and save to txt file"""
    
    # Get statistics
    comp_diff_stats = df['Compensation Difference'].describe() if df['Compensation Difference'].notna().sum() > 0 else None
    cash_diff = df['TRM Level Cash'] - df['TRM Cash']
    cash_diff_stats = cash_diff.describe() if df['TRM Level Cash'].notna().sum() > 0 and df['TRM Cash'].notna().sum() > 0 else None
    
    report_content = f"""CANDIDATE COMPOSITION DATA 2025 - CLEANING SUMMARY REPORT
========================================================
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
--------
Input Data: {original_count} total records
Processing Date: {pd.Timestamp.now().strftime('%Y-%m-%d')}
Script: clean_candidate.py

DATA FILTERING
--------------
• {filtered_count} incomplete records removed → saved to 'incomplete_candidate_records.csv'
• {len(df)} complete records processed → saved to 'complete_candidate_records.csv'

Records were filtered out if they had blank or 'Unknown' values in critical fields:
- Location (blank/Unknown)
- High Potential? (blank)
- Geo Factor (blank)
- Comp Type (blank) 
- Current Level (blank)
- $ Base Comp (blank)

CLEANING OPERATIONS PERFORMED
-----------------------------
1. ✅ Candidate Number column added (extracted from names)
   - Range: Candidate 1 to Candidate {original_count}

2. ✅ Missing dates filled via linear interpolation
   - Final result: {df['Date'].isna().sum()} missing dates

3. ✅ Incomplete records filtered out
   - {filtered_count} records moved to separate file
   - {len(df)} complete records retained for processing

4. ✅ Geo Factor values updated
   - Geographic coverage: {df['Location'].nunique()} unique locations
   - Tech/Non-tech distribution: {df['Tech/Non-Tech/Quota Carrying'].value_counts().to_dict()}

5. ✅ Compensation Difference calculated (TRM Cash - $ Base Comp)
   - {df['Compensation Difference'].notna().sum()} compensation differences calculated successfully
   - {df['Compensation Difference'].isna().sum()} records unable to calculate (missing/invalid base compensation)

6. ✅ TRM Cash values updated using payband database
   - Formula: Final Pay Band × Current Level × Geo Factor
   - {df['TRM Cash'].notna().sum()} records have TRM Cash values

7. ✅ TRM Level Cash column added
   - Formula: Final Pay Band × TRM Level × Geo Factor
   - {df['TRM Level Cash'].notna().sum()} records had TRM Level Cash calculated
   - {df['TRM Level Cash'].isna().sum()} records with missing TRM Level Cash

FINAL DATASET STATISTICS
------------------------
Records: {len(df)} complete records ({len(df.columns)} columns)
Date Range: {df['Date'].min()} to {df['Date'].max()}
Data Quality: {df['Date'].isna().sum()} missing dates, {df['Candidate Number'].isna().sum()} missing candidate numbers, {df['Geo Factor'].isna().sum()} missing geo factors

COMPENSATION ANALYSIS
--------------------"""

    if comp_diff_stats is not None:
        report_content += f"""
Compensation Difference (TRM Cash - $ Base Comp):
- Mean: ${comp_diff_stats['mean']:,.2f}
- Median: ${comp_diff_stats['50%']:,.2f}
- Minimum: ${comp_diff_stats['min']:,.2f}
- Maximum: ${comp_diff_stats['max']:,.2f}
- Records calculated: {df['Compensation Difference'].notna().sum()}/{len(df)}"""

    if cash_diff_stats is not None:
        same_values = (abs(cash_diff) < 0.01).sum()
        different_values = (abs(cash_diff) >= 0.01).sum()
        report_content += f"""

TRM Level Cash vs TRM Cash Comparison:
- Mean difference: ${cash_diff_stats['mean']:,.2f}
- Median difference: ${cash_diff_stats['50%']:,.2f}
- Minimum difference: ${cash_diff_stats['min']:,.2f}
- Maximum difference: ${cash_diff_stats['max']:,.2f}
- Records with identical values: {same_values} (current level = target level)
- Records with different values: {different_values} (promotion/demotion potential)"""

    completion_rate = (len(df) / original_count * 100) if original_count > 0 else 0
    level_alignment_rate = (same_values / len(df) * 100) if cash_diff_stats is not None and len(df) > 0 else 0
    
    report_content += f"""

KEY INSIGHTS
------------
1. Data Completeness: {completion_rate:.1f}% of original records ({len(df)}/{original_count}) had complete critical data
2. Level Alignment: {level_alignment_rate:.1f}% of candidates ({same_values}/{len(df)}) are already at their target TRM level"""

    if comp_diff_stats is not None:
        report_content += f"""
3. Compensation Gap: Average ${comp_diff_stats['mean']:,.0f} difference between TRM Cash and current base compensation"""
    
    if cash_diff_stats is not None:
        report_content += f"""
4. Promotion Potential: {different_values} candidates show difference between current and TRM level compensation"""

    report_content += f"""
5. Geographic Distribution: Data spans {df['Location'].nunique()} locations with {"strong tech role representation" if df[df['Tech/Non-Tech/Quota Carrying'] == 'Tech'].shape[0] / len(df) > 0.8 else "mixed tech/non-tech roles"}

OUTPUT FILES GENERATED
---------------------
• complete_candidate_records.csv - Clean dataset ({len(df)} records)
• incomplete_candidate_records.csv - Filtered out records ({filtered_count} records)  
• {summary_file} - This summary report

RECOMMENDATIONS
---------------
1. Review incomplete_candidate_records.csv to determine if missing data can be obtained
2. Investigate the {different_values if cash_diff_stats is not None else "N/A"} candidates with level misalignment for potential promotions
3. Analyze compensation gaps for budget planning and equity adjustments
4. Verify payband matches for data accuracy

========================================================
End of Report"""

    # Write report to file
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 Cleaning summary report saved as: {summary_file}")
    return summary_file

if __name__ == "__main__":
    # Run the cleaning process
    try:
        # Get original counts for reporting
        original_df = pd.read_csv('candidate_comp_data_2025.csv')
        original_count = len(original_df)
        
        cleaned_df = clean_candidate_data()
        show_cleaning_summary(cleaned_df)
        
        # Calculate filtered count
        filtered_count = original_count - len(cleaned_df)
        
        # Generate summary report
        create_cleaning_summary_report(cleaned_df, original_count, filtered_count)
        
        print("\n🎉 Data cleaning completed successfully!")
        
    except FileNotFoundError:
        print("❌ Error: candidate_comp_data_2025.csv not found in current directory")
    except Exception as e:
        print(f"❌ Error during cleaning: {str(e)}")