#!/usr/bin/env python3
"""
TRM Labs Active Employee Compensation Calculator
===============================================

Script that:
1. Extracts current headcount from Excel
2. Matches with payband database using level, seniority, and role
3. Applies geo factor adjustments based on country and tech/non-tech classification
4. Calculates adjusted compensation for all active employees
5. Includes start date and calculates tenure ranges (0-90 days, 3-6 months, 6-12 months, 1-2 years, 2-5 years, 5+ years)

Usage:
    python 5active_comp.py

Author: Ana Avendano
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, timedelta

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
    """Get the Excel file path using relative path from script directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_filename = "HR Comp Data & HC __ People Analytics Exercise.xlsx"
    file_path = os.path.join(script_dir, excel_filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    return file_path

def load_payband_data():
    """Load payband database from CSV"""
    payband_file = 'payband_database_complete.csv'
    if not os.path.exists(payband_file):
        raise FileNotFoundError(f"Payband database not found: {payband_file}. Please run script 3 first.")
    
    return pd.read_csv(payband_file)

def load_geofactors_data():
    """Load geofactors data from CSV"""
    geo_file = 'geofactors_data.csv'
    if not os.path.exists(geo_file):
        raise FileNotFoundError(f"Geofactors data not found: {geo_file}. Please run script 2 first.")
    
    return pd.read_csv(geo_file)

def parse_level_distinction(level_distinction):
    """
    Parse level distinction into level code and seniority
    Examples: 'L4 Seasoned' -> ('L4', 'Seasoned')
              'L3' -> ('L3', None)
              'M4 Early' -> ('M4', 'Early')
    """
    if pd.isna(level_distinction):
        return None, None
    
    level_str = str(level_distinction).strip()
    
    # Try to match pattern: Level + Seniority
    match = re.match(r'^([LM]\d+)\s+(Early|Seasoned|Veteran)$', level_str)
    if match:
        return match.group(1), match.group(2)
    
    # Try to match just level code
    match = re.match(r'^([LM]\d+)$', level_str)
    if match:
        return match.group(1), None
    
    return None, None

def determine_tech_classification(payband_granular):
    """
    Determine if a role is tech or non-tech based on payband granular
    Non-tech: Operations - Finance - Accounting - Mgmt, Operations - Finance - FP&A - Mgmt
    Tech: Everything else
    """
    if pd.isna(payband_granular):
        return None
    
    payband_str = str(payband_granular).strip()
    
    non_tech_roles = [
        'Operations - Finance - Accounting - Mgmt',
        'Operations - Finance - FP&A - Mgmt'
    ]
    
    return 'Non-Tech' if payband_str in non_tech_roles else 'Tech'

def calculate_tenure_range(start_date):
    """
    Calculate tenure range based on start date and today's date
    Returns: 0-90 days, 3-6 months, 6-12 months, 1-2 years, 2-5 years, 5+ years
    """
    if pd.isna(start_date):
        return 'Unknown'
    
    try:
        # Convert to datetime if it's not already
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        elif not isinstance(start_date, datetime):
            start_date = pd.to_datetime(start_date)
        
        # Calculate days of tenure
        today = datetime.now()
        tenure_days = (today - start_date).days
        
        if tenure_days < 0:
            return 'Future Start Date'
        elif tenure_days <= 90:
            return '0-90 days'
        elif tenure_days <= 180:  # ~6 months
            return '3-6 months'
        elif tenure_days <= 365:  # ~12 months
            return '6-12 months'
        elif tenure_days <= 730:  # ~2 years
            return '1-2 years'
        elif tenure_days <= 1825:  # ~5 years
            return '2-5 years'
        else:
            return '5+ years'
    
    except Exception as e:
        print(f"Warning: Could not parse start date '{start_date}': {e}")
        return 'Invalid Date'

def match_payband_compensation(employee_row, payband_df):
    """
    Match employee with payband data to get compensation
    """
    level_code, seniority_name = parse_level_distinction(employee_row['Level distinction'])
    payband_granular = employee_row['Payband (granular)']
    
    if not level_code or pd.isna(payband_granular):
        return None, None, None, None
    
    # If no seniority specified, we'll try to find a match with any seniority
    if seniority_name:
        # Exact match with seniority
        match = payband_df[
            (payband_df['level_code'] == level_code) &
            (payband_df['seniority_name'] == seniority_name) &
            (payband_df['role_category'] == payband_granular)
        ]
    else:
        # No seniority specified, try to find any match for that level and role
        match = payband_df[
            (payband_df['level_code'] == level_code) &
            (payband_df['role_category'] == payband_granular)
        ]
        # If multiple matches, prefer 'Seasoned' as default
        if len(match) > 1:
            seasoned_match = match[match['seniority_name'] == 'Seasoned']
            if len(seasoned_match) > 0:
                match = seasoned_match
            else:
                match = match.iloc[[0]]  # Take first match
    
    if len(match) > 0:
        row = match.iloc[0]
        return row['cash_base'], row['equity_value'], row['seniority_name'], row['level_code']
    
    return None, None, None, None

def get_geo_factor(country, tech_classification, geofactors_df):
    """
    Get geo factor for a country and tech classification
    """
    if pd.isna(country) or not tech_classification:
        return 1.0
    
    # Find matching country
    country_match = geofactors_df[geofactors_df['Country'].str.strip() == country.strip()]
    
    if len(country_match) == 0:
        print(f"Warning: Country '{country}' not found in geofactors. Using 1.0")
        return 1.0
    
    row = country_match.iloc[0]
    
    if tech_classification == 'Tech':
        return row['Geo Factor for tech roles (Including Solutions Engineering, but excluding P. I.)']
    else:  # Non-Tech
        return row['Geo Factor for non tech roles']

def calculate_active_compensation():
    """Main function to calculate active employee compensation"""
    start_time = datetime.now()
    
    print_banner("TRM LABS ACTIVE EMPLOYEE COMPENSATION CALCULATOR")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Load data
        print_section("Loading data...")
        file_path = get_excel_file_path()
        
        # Load current headcount
        print("📊 Loading current headcount...")
        current_hc = pd.read_excel(file_path, sheet_name='Current Headcount')
        print(f"Loaded {len(current_hc)} active employees")
        
        # Load payband database
        print("💰 Loading payband database...")
        payband_df = load_payband_data()
        print(f"Loaded {len(payband_df)} payband records")
        
        # Load geofactors
        print("🌍 Loading geofactors...")
        geofactors_df = load_geofactors_data()
        print(f"Loaded {len(geofactors_df)} geofactor records")
        
        # Process each employee
        print_section("Processing employee compensation...")
        
        results = []
        match_stats = {'matched': 0, 'unmatched': 0}
        
        for idx, employee in current_hc.iterrows():
            # Parse level distinction
            level_code, seniority_name = parse_level_distinction(employee['Level distinction'])
            
            # Determine tech classification
            tech_classification = determine_tech_classification(employee['Payband (granular)'])
            
            # Calculate tenure range from start date
            start_date = employee.get('Start Date', None)
            tenure_range = calculate_tenure_range(start_date)
            
            # Match with payband
            payband_cash, payband_equity, matched_seniority, matched_level = match_payband_compensation(employee, payband_df)
            
            # Get geo factor
            geo_factor = get_geo_factor(employee['Country'], tech_classification, geofactors_df)
            
            # Calculate adjusted compensation
            if payband_cash is not None and payband_equity is not None:
                adjusted_base_comp = payband_cash * geo_factor
                adjusted_equity = payband_equity * geo_factor
                match_status = 'Matched'
                match_stats['matched'] += 1
            else:
                adjusted_base_comp = None
                adjusted_equity = None
                match_status = 'No Match'
                match_stats['unmatched'] += 1
            
            # Store result
            result = {
                'Employee Name': employee['Employee Name'],
                'Department': employee['Department'],
                'Org': employee['Org'],
                'Country': employee['Country'],
                'Start Date': start_date,
                'Tenure Range': tenure_range,
                'Level distinction': employee['Level distinction'],
                'Parsed Level Code': level_code,
                'Parsed Seniority': seniority_name,
                'Matched Seniority': matched_seniority,
                'Payband (granular)': employee['Payband (granular)'],
                'Tech Classification': tech_classification,
                'Current Base Comp (USD)': employee.get('Base Annual Compensation\n(USD)', None),
                'Current Equity Value': employee.get('Current total Equity \n(value)', None),
                'Target Base Comp (Geo-Adjusted)': adjusted_base_comp,
                'Target Equity Value (Geo-Adjusted)': adjusted_equity,
                'Geo Factor': geo_factor,
                'Raw Payband Base Comp': payband_cash,
                'Raw Payband Equity Value': payband_equity,
                'Perf Score H1 25': employee.get('Perf Score H1 25', None),
                'Match Status': match_status
            }
            results.append(result)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        output_file = 'active_employee_compensation.csv'
        results_df.to_csv(output_file, index=False)
        
        # Summary statistics
        print_section("Processing Summary")
        print(f"✅ Total employees processed: {len(results_df)}")
        print(f"✅ Successfully matched: {match_stats['matched']}")
        print(f"❌ Could not match: {match_stats['unmatched']}")
        print(f"📈 Match rate: {(match_stats['matched']/len(results_df)*100):.1f}%")
        
        # Show tech vs non-tech breakdown
        tech_breakdown = results_df['Tech Classification'].value_counts()
        print(f"\nTech Classification Breakdown:")
        for classification, count in tech_breakdown.items():
            print(f"  {classification}: {count} employees")
        
        # Show country breakdown
        print(f"\nCountry Breakdown:")
        country_counts = results_df['Country'].value_counts().head(10)
        for country, count in country_counts.items():
            print(f"  {country}: {count} employees")
        
        # Show tenure range breakdown
        print(f"\nTenure Range Breakdown:")
        tenure_counts = results_df['Tenure Range'].value_counts()
        # Sort by logical order
        tenure_order = ['0-90 days', '3-6 months', '6-12 months', '1-2 years', '2-5 years', '5+ years', 'Unknown', 'Invalid Date', 'Future Start Date']
        for tenure in tenure_order:
            if tenure in tenure_counts.index:
                count = tenure_counts[tenure]
                print(f"  {tenure}: {count} employees")
        
        # Show unmatched employees details
        if match_stats['unmatched'] > 0:
            print(f"\n❌ Unmatched Employees:")
            unmatched = results_df[results_df['Match Status'] == 'No Match']
            for _, emp in unmatched.iterrows():
                print(f"  {emp['Employee Name']}: Level='{emp['Level distinction']}', Role='{emp['Payband (granular)']}'"[:100])
        
        # Show sample of matched employees
        matched_df = results_df[results_df['Match Status'] == 'Matched']
        if len(matched_df) > 0:
            print(f"\n🎯 Sample of Matched Employees:")
            sample_cols = ['Employee Name', 'Tenure Range', 'Level distinction', 'Raw Payband Base Comp', 'Geo Factor', 'Target Base Comp (Geo-Adjusted)']
            print(matched_df[sample_cols].head(5))
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_banner("COMPENSATION CALCULATION COMPLETE")
        print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print(f"\n📁 Output file: {output_file}")
        
        file_size = os.path.getsize(output_file)
        print(f"📊 File size: {file_size:,} bytes")
        
        print("\n🔗 Repository: https://github.com/datadoesntlie/trm-labs-people-analytics")
        print("\nActive compensation calculation complete! 🚀")
        
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ {str(e)}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    # Change to script directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        exit_code = calculate_active_compensation()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Calculation interrupted by user.")
        print("Partial results may be available.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error in calculation: {str(e)}")
        exit(1)