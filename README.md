# toc-tools

tools to help inventory and organize a toc

### Initial setup for toc-tools

To run any of the scripts in this repo, first follow these steps.

1. Create an environment:

    **Windows (PowerShell):**
    ```powershell
    python -m venv .venv
    # If you encounter execution policy errors, first fix the policy:
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    # Then activate the environment:
    & ".venv\scripts\Activate.ps1"
    # Alternative: If still having issues, you can run Python directly from the venv
    # Use: & ".venv\scripts\python.exe" instead of just "python" in subsequent commands
    ```

    **Mac/Linux (bash/zsh):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

1. Install packages into environment:

    **Windows:**
    ```powershell
    pip install -r requirements.txt
    # Or if using the direct Python method: & ".venv\scripts\python.exe" -m pip install -r requirements.txt
    ```

    **Mac/Linux:**
    ```bash
    pip install -r requirements.txt
    ```

1. Rename the **env-sample.txt** file in this repo to **.env**

1. Modify the values as described in following sections.


## Step 1: Build a CSV file showing all the files in your TOC

This script runs quickly, even for large TOCs.  It creates a spreadsheet showing the TOC structure along with the file name and URL.  

### Setup for build spreadsheet

1. In your **.env** file, add:

    * TOC_FILE - local path to your toc file
    * URL_PATH - https://learn.microsoft.com/  path to the homepage for your toc
    * OUTPUT_FILE= - file you want to create

### Build the spreadsheet

1. Build the spreadsheet:

    **Windows:**
    ```powershell
    python build-spreadsheet.py
    # Or if using direct method: & ".venv\scripts\python.exe" build-spreadsheet.py
    ```

    **Mac/Linux:**
    ```bash
    python build-spreadsheet.py
    ```

This script will:
    - Read the initial toc file (this is a local file, make sure you're on the branch you want results for)
    - Iterate through any nested toc files if found
    - Flatten the toc structure into a single entry per item
    - Create a CSV file with results


## Step 2: Add metadata from files

Extract metadata from the front matter of markdown files and add it to your spreadsheet. This script reads each file referenced in your CSV and extracts `ms.author`, `ms.topic`, `author`, `description`,  `pivot` (zone_pivot_groups), and `hub-only` metadata. This also uses local files.

### Setup for metadata extraction

1. In your **.env** file, add:
    * BASE_PATH - the root directory where your markdown files are located
    * METADATA_OUTPUT_FILE - the name of the enhanced CSV file (optional, defaults to toc_with_metadata.csv)

### Extract metadata

1. To add metadata to your spreadsheet:

    **Windows:**
    ```powershell
    python add-metadata.py
    # Or if using direct method: & ".venv\scripts\python.exe" add-metadata.py
    ```

    **Mac/Linux:**
    ```bash
    python add-metadata.py
    ```

    This script will:
    - Read your existing CSV file
    - Look up each markdown file based on the Href column
    - Extract YAML front matter metadata
    - Add columns for ms.author, ms.topic, description, pivot, pivot groups, and file_found
    - Create an enhanced CSV with the metadata

## Run Complete Analysis Pipeline

For convenience, you can run all three steps (build spreadsheet, add metadata, add content analysis) with a single command using the comprehensive pipeline script.

### Setup for complete pipeline

1. Ensure your **.env** file has all required variables:
    * TOC_FILE - local path to your toc file
    * URL_PATH - <https://learn.microsoft.com/> path to the homepage for your toc
    * OUTPUT_FILE - file you want to create for the initial spreadsheet
    * BASE_PATH - the root directory where your markdown files are located
    * METADATA_OUTPUT_FILE - enhanced CSV with metadata (for individual script runs)
    * CONTENT_OUTPUT_FILE - final CSV with content analysis (for individual script runs)

**Note:** When using `run-all-analysis.py`, the pipeline automatically overrides the output file settings to use a unified workflow where each step enhances the same file (OUTPUT_FILE). When running scripts individually, each creates its own separate output file as configured in your .env.
    * CONTENT_OUTPUT_FILE - final CSV with content analysis (optional)

### Run complete analysis

1. To run the complete pipeline:

    **Windows:**
    ```powershell
    python run-all-analysis.py
    # Or if using direct method: & ".venv\scripts\python.exe" run-all-analysis.py
    ```

    **Mac/Linux:**
    ```bash
    python run-all-analysis.py
    ```

    Or to skip specific steps:

    **Windows:**
    ```powershell
    python run-all-analysis.py --skip-content    # Skip content analysis
    python run-all-analysis.py --skip-metadata   # Skip metadata extraction
    python run-all-analysis.py --skip-build      # Skip initial build
    ```

    **Mac/Linux:**
    ```bash
    python run-all-analysis.py --skip-content    # Skip content analysis
    python run-all-analysis.py --skip-metadata   # Skip metadata extraction
    python run-all-analysis.py --skip-build      # Skip initial build
    ```

    This script will:
    * Run build-spreadsheet.py to create the initial TOC spreadsheet
    * Run add-metadata.py to extract metadata from markdown files
    * Run add-content-analysis.py to analyze content for tabs and images
    * Show a summary of all created files
    * Provide detailed progress and error reporting for each step





