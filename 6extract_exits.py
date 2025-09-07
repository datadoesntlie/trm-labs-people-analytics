#!/usr/bin/env python3
"""
TRM Labs Exits Data Extraction Script
====================================

Script that extracts employee exits data from 2024 onwards from Excel file.

Usage:
    python 6extract_exits.py

Author: Ana Avendano
"""

import pandas as pd
import numpy as np
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
    """Get the Excel file path using relative path from script directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    excel_filename = "HR Comp Data & HC __ People Analytics Exercise.xlsx"
    file_path = os.path.join(script_dir, excel_filename)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    return file_path

def extract_exits_data():
    """Main function to extract exits data"""
    start_time = datetime.now()
    
    print_banner("TRM LABS EXITS DATA EXTRACTION")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get the Excel file path
        file_path = get_excel_file_path()
        print(f"\nUsing Excel file: {os.path.basename(file_path)}")
        
        print_section("=== EXTRACTING EXITS - 2024 ONWARDS ===")
        
        # Read the Exits sheet
        exits_data = pd.read_excel(file_path, sheet_name='Exits - 2024 onwards')
        
        print(f"Loaded {len(exits_data)} exit records with {len(exits_data.columns)} columns")
        
        # Show basic info about the data
        print(f"\nColumns in the dataset:")
        for i, col in enumerate(exits_data.columns, 1):
            print(f"{i:2d}. {col}")
        
        # Convert date columns to datetime for better analysis
        date_columns = []
        for col in exits_data.columns:
            if 'date' in col.lower() or 'start' in col.lower() or 'last' in col.lower():
                try:
                    exits_data[col] = pd.to_datetime(exits_data[col], errors='coerce')
                    date_columns.append(col)
                    print(f"✅ Converted '{col}' to datetime")
                except:
                    pass
        
        if date_columns:
            print(f"\nDate columns converted: {date_columns}")
        
        # Show data types
        print(f"\nData types:")
        for col in exits_data.columns:
            dtype_str = str(exits_data[col].dtype)
            print(f"  {col}: {dtype_str}")
        
        # Show date range if date columns exist
        if date_columns:
            print(f"\nDate ranges:")
            for col in date_columns:
                if exits_data[col].notna().any():
                    min_date = exits_data[col].min()
                    max_date = exits_data[col].max()
                    print(f"  {col}: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        # Save to CSV
        output_file = 'exits_2024_onwards.csv'
        exits_data.to_csv(output_file, index=False)
        
        print(f"\n✅ Exits data exported to: {output_file}")
        print(f"📊 Dataset contains {len(exits_data)} records")
        
        # Show summary statistics
        print(f"\nSummary Statistics:")
        
        # Count by department if column exists
        if 'Department' in exits_data.columns:
            dept_counts = exits_data['Department'].value_counts()
            print(f"\nExits by Department:")
            for dept, count in dept_counts.head(10).items():
                print(f"  {dept}: {count} exits")
        
        # Count by organization if column exists
        if 'Org' in exits_data.columns:
            org_counts = exits_data['Org'].value_counts()
            print(f"\nExits by Organization:")
            for org, count in org_counts.items():
                print(f"  {org}: {count} exits")
        
        # Count by country if column exists
        if 'Country' in exits_data.columns:
            country_counts = exits_data['Country'].value_counts()
            print(f"\nExits by Country:")
            for country, count in country_counts.head(10).items():
                print(f"  {country}: {count} exits")
        
        # Show sample of data
        print(f"\nPreview of first 5 records:")
        # Display only first few columns to avoid overwhelming output
        display_cols = list(exits_data.columns)[:6]
        print(exits_data[display_cols].head())
        
        # Summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        print_banner("EXITS DATA EXTRACTION COMPLETE")
        print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total duration: {duration}")
        print(f"\n📁 Output file: {output_file}")
        
        file_size = os.path.getsize(output_file)
        print(f"📊 File size: {file_size:,} bytes")
        
        print("\n🔗 Repository: https://github.com/datadoesntlie/trm-labs-people-analytics")
        print("\nExits data extraction complete! 🚀")
        
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
        exit_code = extract_exits_data()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Extraction interrupted by user.")
        print("Partial results may be available.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error in extraction: {str(e)}")
        exit(1)