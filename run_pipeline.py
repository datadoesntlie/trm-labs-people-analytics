#!/usr/bin/env python3
"""
TRM Labs People Analytics Pipeline
==================================

Automated pipeline to run all data extraction and cleaning scripts in the correct sequence:
1. Extract candidate data
2. Extract geofactors  
3. Extract payband data
4. Clean candidate data

Usage:
    python run_pipeline.py

Author: Ana Avendano
"""

import subprocess
import sys
import os
from datetime import datetime

def print_banner(message):
    """Print a formatted banner message"""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_step(step_num, total_steps, description):
    """Print step information"""
    print(f"\n[STEP {step_num}/{total_steps}] {description}")
    print("-" * 60)

def run_script(script_name, description):
    """
    Run a Python script and return success/failure status
    
    Args:
        script_name (str): Name of the script file
        description (str): Description of what the script does
        
    Returns:
        bool: True if script ran successfully, False otherwise
    """
    print(f"🚀 Running: {script_name}")
    print(f"📋 Purpose: {description}")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            [sys.executable, script_name], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Print the output
        if result.stdout:
            print("📄 Output:")
            print(result.stdout)
        
        print(f"✅ {script_name} completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    
    except FileNotFoundError:
        print(f"❌ Script not found: {script_name}")
        print("Make sure the script exists in the current directory.")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error running {script_name}: {str(e)}")
        return False

def check_dependencies():
    """Check if all required script files exist"""
    required_scripts = [
        "1extract_candidate_data.py",
        "2extract_geofactors.py", 
        "3extract_payband.py",
        "4clean_candidate.py"
    ]
    
    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print("❌ Missing required scripts:")
        for script in missing_scripts:
            print(f"   - {script}")
        return False
    
    return True

def main():
    """Main pipeline execution"""
    start_time = datetime.now()
    
    print_banner("TRM LABS PEOPLE ANALYTICS PIPELINE")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if all required scripts exist
    if not check_dependencies():
        print("\n❌ Pipeline cannot run due to missing scripts.")
        sys.exit(1)
    
    # Define the pipeline steps
    pipeline_steps = [
        {
            "script": "1extract_candidate_data.py",
            "description": "Extract candidate composition data from Excel file"
        },
        {
            "script": "2extract_geofactors.py", 
            "description": "Extract geographic adjustment factors"
        },
        {
            "script": "3extract_payband.py",
            "description": "Extract payband database from HR data"
        },
        {
            "script": "4clean_candidate.py",
            "description": "Clean and validate candidate data with comprehensive reporting"
        }
    ]
    
    total_steps = len(pipeline_steps)
    successful_steps = 0
    failed_steps = []
    
    # Execute each step in sequence
    for i, step in enumerate(pipeline_steps, 1):
        print_step(i, total_steps, step["description"])
        
        success = run_script(step["script"], step["description"])
        
        if success:
            successful_steps += 1
        else:
            failed_steps.append(step["script"])
            print(f"\n⚠️  Step {i} failed. Continuing with remaining steps...")
    
    # Pipeline completion summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_banner("PIPELINE EXECUTION SUMMARY")
    print(f"Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {duration}")
    print(f"Steps completed: {successful_steps}/{total_steps}")
    
    if failed_steps:
        print(f"\n❌ Failed steps:")
        for script in failed_steps:
            print(f"   - {script}")
        
        print(f"\n⚠️  Pipeline completed with {len(failed_steps)} error(s).")
        print("Please check the output above for details on failed steps.")
        sys.exit(1)
    else:
        print("\n🎉 All pipeline steps completed successfully!")
        
        # List output files
        output_files = [
            "candidate_comp_data_2025.csv",
            "geofactors_data.csv", 
            "payband_database_complete.csv",
            "complete_candidate_records.csv",
            "incomplete_candidate_records.csv",
            "candidate_cleaning_report.txt"
        ]
        
        print("\n📁 Generated files:")
        for file in output_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"   ✅ {file} ({size:,} bytes)")
            else:
                print(f"   ❓ {file} (not found)")
        
        print("\n🔗 Repository: https://github.com/datadoesntlie/trm-labs-people-analytics")
        print("\nPipeline execution complete! 🚀")

if __name__ == "__main__":
    # Change to script directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user.")
        print("Partial results may be available.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error in pipeline: {str(e)}")
        sys.exit(1)