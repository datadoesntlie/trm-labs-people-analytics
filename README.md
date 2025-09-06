# TRM Labs - People Analytics Exercise

This repository contains data processing scripts and analysis for the TRM Labs People Analytics Exercise focusing on candidate compensation data cleaning and payband analysis.

## Project Overview

The project consists of several Python scripts that extract, clean, and analyze HR compensation data:

1. **Data Extraction Scripts**:
   - `1extract_candidate_data.py` - Extracts candidate composition data from Excel
   - `2extract_geofactors.py` - Extracts geographic factor data
   - `3extract_payband.py` - Extracts payband information from HR data

2. **Data Cleaning Script**:
   - `4clean_candidate.py` - Main cleaning script that processes candidate data

3. **Data Files**:
   - `candidate_comp_data_2025.csv` - Raw candidate data
   - `geofactors_data.csv` - Geographic adjustment factors
   - `payband_database_complete.csv` - Complete payband database
   - `complete_candidate_records.csv` - Cleaned candidate records
   - `incomplete_candidate_records.csv` - Filtered incomplete records

4. **Reports**:
   - `candidate_cleaning_report.txt` - Detailed cleaning summary report

## Features

### Data Cleaning Operations
- Candidate number extraction and ordering
- Date interpolation for missing values
- Geographic factor updates based on location and role type
- TRM Cash calculation using payband database
- TRM Level Cash calculation for target compensation
- Compensation difference analysis
- Data quality filtering and validation

### Key Outputs
- **Complete Records**: Clean dataset with all required fields populated
- **Incomplete Records**: Filtered records requiring additional data
- **Cleaning Report**: Comprehensive analysis with statistics and recommendations

## Usage

1. **Extract Data**:
   ```bash
   python 1extract_candidate_data.py
   python 2extract_geofactors.py
   python 3extract_payband.py
   ```

2. **Clean Data**:
   ```bash
   python 4clean_candidate.py
   ```

3. **Review Results**:
   - Check `complete_candidate_records.csv` for final clean data
   - Review `candidate_cleaning_report.txt` for detailed analysis
   - Examine `incomplete_candidate_records.csv` for data quality issues

## Data Quality Insights

The cleaning process filters records based on critical fields:
- Location (blank/Unknown)
- High Potential status
- Geographic factors
- Compensation type
- Current level
- Base compensation

## Requirements

- Python 3.7+
- pandas
- numpy
- openpyxl (for Excel file processing)

## Author

Ana Avendano - People Analytics Exercise for TRM Labs