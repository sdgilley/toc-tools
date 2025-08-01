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
    
    # Get output file names from environment variables
    output_file = os.getenv("OUTPUT_FILE", "toc.csv")
    metadata_output = os.getenv("METADATA_OUTPUT_FILE", "toc_with_metadata.csv")
    content_output = os.getenv("CONTENT_OUTPUT_FILE", "toc_with_content.csv")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_to_check = [
        (output_file, "Initial TOC spreadsheet"),
        (metadata_output, "TOC with metadata"),
        (content_output, "TOC with content analysis"),
        (metadata_output.replace('.csv', '-pivots.csv'), "Pivot groups (if created)")
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
    
    args = parser.parse_args()
    
    print("🚀 Starting TOC Analysis Pipeline")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check environment configuration
    if not check_environment():
        sys.exit(1)
    
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
    print("You can now open the CSV files to review your TOC structure, metadata, and content analysis.")

if __name__ == "__main__":
    main()
