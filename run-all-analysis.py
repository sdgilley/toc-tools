#!/usr/bin/env python3
"""
This script runs the complete TOC analysis pipeline in three steps:
1. Build spreadsheet from TOC files
2. Add metadata extraction from markdown files
3. Add content analysis (tabs and images)

Usage:
    python run-all-analysis.py [--skip-build] [--skip-metadata] [--skip-content]

Options:
    --skip-build      Skip the spreadsheet building step
    --skip-metadata   Skip the metadata extraction step
    --skip-content    Skip the content analysis step
    --help           Show this help message
"""

import os
import sys
import argparse
import subprocess
import time
import dotenv
from pathlib import Path

# Load environment variables from .env file
dotenv.load_dotenv()

def run_script(script_name, description):
    """
    Run a Python script and handle any errors.
    
    Args:
        script_name (str): Name of the script to run
        description (str): Description of what the script does
        
    Returns:
        bool: True if successful, False if failed
    """
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"Running: {script_name}")
    print(f"{'='*60}")
    
    try:
        # Run the script in the same directory
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,  # Show output in real-time
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} completed successfully!")
            return True
        else:
            print(f"\n❌ {description} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False

def check_environment():
    """
    Check if required environment variables are set.
    
    Returns:
        bool: True if environment is properly configured
    """
    print("Checking environment configuration...")
    
    required_vars = {
        'TOC_FILE': 'Path to your TOC file',
        'URL_PATH': 'URL path for your documentation',
        'BASE_PATH': 'Base path where markdown files are located'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  {var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\nPlease check your .env file and ensure all required variables are set.")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def show_output_files():
    """
    Show the output files that were created.
    """
    print(f"\n{'='*60}")
    print("OUTPUT FILES CREATED:")
    print(f"{'='*60}")
    
    # In pipeline mode, we use the base output file for everything
    base_output_file = os.getenv("OUTPUT_FILE", "toc.csv")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_to_check = [
        (base_output_file, "Complete TOC with all analysis (build + metadata + content)"),
        (base_output_file.replace('.csv', '-pivots.csv'), "Pivot groups (if created)"),
        (base_output_file.replace('.csv', '.xlsx'), "Excel analysis file (if created)")
    ]
    
    for filename, description in files_to_check:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ {description}: {filename} ({file_size:,} bytes)")
        else:
            print(f"⚠️  {description}: {filename} (not found)")

def main():
    """
    Main function to run the complete analysis pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Run complete TOC analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--skip-build', action='store_true',
                        help='Skip the spreadsheet building step')
    parser.add_argument('--skip-metadata', action='store_true',
                        help='Skip the metadata extraction step')
    parser.add_argument('--skip-content', action='store_true',
                        help='Skip the content analysis step')
    parser.add_argument('--skip-excel', action='store_true',
                        help='Skip creating Excel file with multiple tabs')
    parser.add_argument('--merge-engagement', action='store_true', default=True,
                        help='Merge engagement stats into analysis (default: off)')
    
    args = parser.parse_args()
    
    print("🚀 Starting TOC Analysis Pipeline")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check environment configuration
    if not check_environment():
        sys.exit(1)
    
    # Override environment variables for unified pipeline workflow
    # Each step will build on the previous step using the same file
    base_output_file = os.getenv("OUTPUT_FILE", "toc.csv")
    print(f"📝 Setting unified output file: {base_output_file}")
    print("   (Each step will enhance the same file)")
    
    # Set environment variables for the pipeline run
    os.environ["METADATA_FILE"] = base_output_file  # Metadata script reads from build output
    os.environ["METADATA_OUTPUT_FILE"] = base_output_file  # Metadata script writes to same file
    os.environ["CONTENT_FILE"] = base_output_file  # Content script reads from metadata output
    os.environ["CONTENT_OUTPUT_FILE"] = base_output_file  # Content script writes to same file
    
    steps_run = 0
    steps_failed = 0
    
    # Step 1: Build spreadsheet
    if not args.skip_build:
        if run_script("build-spreadsheet.py", "Building TOC Spreadsheet"):
            steps_run += 1
        else:
            steps_failed += 1
            print("\n❌ Stopping pipeline due to build failure.")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping spreadsheet building step")
    
    # Step 2: Add metadata
    if not args.skip_metadata:
        if run_script("add-metadata.py", "Adding Metadata from Files"):
            steps_run += 1
        else:
            steps_failed += 1
            print("\n❌ Stopping pipeline due to metadata extraction failure.")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping metadata extraction step")
    
    # Step 3: Add content analysis
    if not args.skip_content:
        if run_script("add-content-analysis.py", "Adding Content Analysis"):
            steps_run += 1
        else:
            steps_failed += 1
            print("\n⚠️  Content analysis failed, but continuing...")
    else:
        print("\n⏭️  Skipping content analysis step")
    
    # Step 4: Create Excel file (by default, unless skipped)
    if not args.skip_excel:
        print(f"\n{'='*60}")
        print("STEP: Creating Excel Analysis File")
        print(f"{'='*60}")
        try:
            # Import the function from add-metadata.py
            import importlib.util
            spec = importlib.util.spec_from_file_location("add_metadata", 
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "add-metadata.py"))
            add_metadata_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(add_metadata_module)
            # Create Excel file using the base output file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, base_output_file)
            # Set env var to control engagement merge
            os.environ["MERGE_ENGAGEMENT"] = "1" if args.merge_engagement else "0"
            excel_path = add_metadata_module.create_excel_analysis(csv_path, base_output_file)
            if excel_path:
                print(f"\n✅ Excel file created successfully: {os.path.basename(excel_path)}")
                steps_run += 1
            else:
                print(f"\n❌ Failed to create Excel file")
                steps_failed += 1
        except Exception as e:
            print(f"\n❌ Error creating Excel file: {e}")
            print("💡 Tip: Install openpyxl with 'pip install openpyxl' for Excel support")
            steps_failed += 1
    else:
        print("\n⏭️  Skipping Excel file creation")
    
    # Show summary
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETED!")
    print(f"{'='*60}")
    print(f"Total time: {duration:.1f} seconds")
    print(f"Steps completed: {steps_run}")
    if steps_failed > 0:
        print(f"Steps failed: {steps_failed}")
    
    # Show output files
    show_output_files()
    
    print(f"\n📊 Your TOC analysis is complete!")
    if not args.skip_excel:
        print("You can now open the Excel file for comprehensive analysis with multiple tabs,")
        print("or use the CSV files for detailed data processing.")
    else:
        print("You can now open the CSV files to review your TOC structure, metadata, and content analysis.")
        print("💡 Tip: Remove --skip-excel flag to also create an Excel file with multiple tabs for easier analysis.")

if __name__ == "__main__":
    main()
