#!/usr/bin/env python3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import calendar

# Read the Excel file
file_path = "/Users/anaavendano/Documents/TMRL/HR Comp Data & HC __ People Analytics Exercise.xlsx"

# Read both sheets
current_hc = pd.read_excel(file_path, sheet_name='Current Headcount')
exits = pd.read_excel(file_path, sheet_name='Exits - 2024 onwards')

# Convert date columns to datetime
current_hc['Start Date'] = pd.to_datetime(current_hc['Start Date'])
exits['Start Date'] = pd.to_datetime(exits['Start Date'])
exits['Last Date'] = pd.to_datetime(exits['Last Date'])

print("Data loaded successfully!")
print(f"Current headcount: {len(current_hc)} employees")
print(f"Exits: {len(exits)} employees")

# Generate detailed historical employee lists for each month
from datetime import datetime
import calendar

# Find the earliest start date to determine how far back to go
earliest_current = current_hc['Start Date'].min()
earliest_exits = exits['Start Date'].min()
earliest_start = min(earliest_current, earliest_exits)

print(f"Earliest start date found: {earliest_start}")

# Find the latest start date to determine end date
latest_current = current_hc['Start Date'].max()
print(f"Latest start date found: {latest_current}")

# Start from earliest start date and go forward to the latest start date + 1 month buffer
end_date = datetime(latest_current.year, latest_current.month, 1)
# Add one month buffer to ensure we capture the full month of the latest hire
if end_date.month == 12:
    end_date = datetime(end_date.year + 1, 1, 1)
else:
    end_date = datetime(end_date.year, end_date.month + 1, 1)
start_year = earliest_start.year
start_month = earliest_start.month

# Calculate total months to cover
total_months = (end_date.year - start_year) * 12 + (end_date.month - start_month) + 1
print(f"Generating data for {total_months} months from {calendar.month_name[start_month]} {start_year} to {calendar.month_name[end_date.month]} {end_date.year}")

all_employee_records = []

for i in range(total_months):
    # Calculate the target month and year properly - going forward from earliest date
    target_year = start_year
    target_month = start_month + i
    
    # Adjust year and month if month exceeds 12
    while target_month > 12:
        target_month -= 12
        target_year += 1
    
    # Get the last day of the target month
    last_day = calendar.monthrange(target_year, target_month)[1]
    month_end = datetime(target_year, target_month, last_day)
    month_name = f"{calendar.month_name[target_month]} {target_year}"
    
    # Get current employees who started by month end
    current_active = current_hc[current_hc['Start Date'] <= month_end].copy()
    current_active['Month'] = month_name
    current_active['Status'] = 'Active'
    
    # Get exited employees who started by month end AND left after month end
    exits_active = exits[
        (exits['Start Date'] <= month_end) & 
        (exits['Last Date'] > month_end)
    ].copy()
    exits_active['Month'] = month_name
    exits_active['Status'] = 'Active (Later Exited)'
    
    # Function to calculate tenure range
    def get_tenure_range(days):
        if days <= 30:
            return "1-30 days"
        elif days <= 90:  # 3 months
            return "1-3 months"
        elif days <= 180:  # 6 months
            return "3-6 months"
        elif days <= 365:  # 1 year
            return "6 months-1 year"
        elif days <= 1825:  # 5 years (365*5)
            return "1-5 years"
        else:
            return "5+ years"
    
    # Add current employees to our records
    for _, emp in current_active.iterrows():
        tenure_days = (month_end - emp['Start Date']).days
        all_employee_records.append({
            'Employee Name': emp['Employee Name'],
            'Month': month_name,
            'Year': target_year,
            'Month_Number': target_month,
            'Start Date': emp['Start Date'].strftime('%Y-%m-%d'),
            'Tenure_Days': tenure_days,
            'Tenure_Range': get_tenure_range(tenure_days),
            'Department': emp.get('Department', ''),
            'Org': emp.get('Org', ''),
            'Manager': emp.get('Manager', ''),
            'Level distinction': emp.get('Level distinction', ''),
            'Country': emp.get('Country', '')
        })
    
    # Add exited employees who were still active in that month
    for _, emp in exits_active.iterrows():
        tenure_days = (month_end - emp['Start Date']).days
        all_employee_records.append({
            'Employee Name': emp['Employee Name'],
            'Month': month_name,
            'Year': target_year,
            'Month_Number': target_month,
            'Start Date': emp['Start Date'].strftime('%Y-%m-%d'),
            'Tenure_Days': tenure_days,
            'Tenure_Range': get_tenure_range(tenure_days),
            'Department': emp.get('Department', ''),
            'Org': emp.get('Org', ''),
            'Manager': emp.get('Manager', ''),
            'Level distinction': emp.get('Level distinction', ''),
            'Country': emp.get('Country', '')
        })
    
    total_count = len(current_active) + len(exits_active)
    print(f"{month_name}: {total_count} employees")

# Create DataFrame with all employee records
detailed_df = pd.DataFrame(all_employee_records)

# Sort by year, month, then employee name
detailed_df = detailed_df.sort_values(['Year', 'Month_Number', 'Employee Name']).reset_index(drop=True)

# Save to CSV
output_file = 'historical_headcount_detailed.csv'
detailed_df.to_csv(output_file, index=False)
print(f"\nDetailed historical employee data saved to: {output_file}")
print(f"Total records: {len(detailed_df)}")
print("\nPreview of generated data:")
print(detailed_df.head(10))