# toc-tools

tools to help inventory and organize a toc

## Initial setup for toc-tools

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

    ```bash
    pip install -r requirements.txt
    ```

1. Rename the **env-sample.txt** file in this repo to **.env**

1. Modify the values as described in following sections.


## Run Complete Analysis Pipeline

Get an excel file with details of your TOC by running the complete pipeline.

### Setup for complete pipeline

1. Ensure your **.env** file has all required variables:
    * TOC_FILE - local path to the toc file you want to inventory
    * URL_PATH - <https://learn.microsoft.com/> path to the homepage for your toc
    * OUTPUT_FILE - CSV file you want to create.  You'll also get an Excel file with this same name containing multiple tabs.
    * BASE_PATH - the root directory where your markdown files are located
    * The rest are only used if you are running the steps separately:
        * METADATA_FILE - file to read for add-metadata (for individual script runs)
        * METADATA_OUTPUT_FILE - enhanced CSV with metadata (for individual script runs)
        * CONTENT_FILE = file to read for content analysis (for individual script runs)
        * CONTENT_OUTPUT_FILE - final CSV with content analysis (for individual script runs)

**Note:** When using `run-all-analysis.py`, the pipeline automatically overrides the output file settings to use a unified workflow where each step enhances the same file (OUTPUT_FILE). When running scripts individually, each creates its own separate output file as configured in your .env.

### Run complete analysis

1. To run the complete pipeline:

    ```bash
    python run-all-analysis.py
    # Or if using direct method: & ".venv\scripts\python.exe" run-all-analysis.py
    ```

    Or to skip specific steps:

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


## Individual steps

The following section shows the various files involved in the pipeline. If modifying the behavior of one of these files, you might want to run them separately.  Otherwise, just use the full analysis pipeline above.  It doesn't take long, even for a large TOC.

### Step 1: Build a CSV file showing all the files in your TOC

This script runs quickly, even for large TOCs.  It creates a spreadsheet showing the TOC structure along with the file name and URL.  

```bash
python build-spreadsheet.py
# Or if using direct method: & ".venv\scripts\python.exe" build-spreadsheet.py
```

This script will:
    - Read the initial toc file (this is a local file, make sure you're on the branch you want results for)
    - Iterate through any nested toc files if found
    - Flatten the toc structure into a single entry per item
    - Create a CSV file with results


### Step 2: Add metadata from files

Extract metadata from the front matter of markdown files and add it to your spreadsheet. This script reads each file referenced in your CSV and extracts `ms.author`, `ms.topic`, `author`, `description`,  `pivot` (zone_pivot_groups), and `hub-only` metadata. This also uses local files.

```bash
python add-metadata.py
```

This script will:

- Read your existing CSV file
- Look up each markdown file based on the Href column
- Extract YAML front matter metadata
- Add columns for ms.author, ms.topic, description, pivot, pivot groups, and file_found
- Create an enhanced CSV with the metadata

When run as a separate step, it reads METADATA_FILE and writes METADATA_OUTPUT_FILE

### Step 3: Add content analysis and create excel file

Analyze the content of markdown files for tabs, images, code blocks, and other elements, then create a comprehensive Excel file with multiple tabs for analysis.

```bash
python add-content-analysis.py
```

This script will:

* Read your enhanced CSV file with metadata
* Analyze each markdown file for content elements:
  * Tabs (tabbed content sections)
  * Images and image references
  * Code blocks and code references
  * Portal steps and other special content
  * Programming languages used in code blocks
* Add content analysis columns to your data
* Create an Excel file with multiple tabs:
  * **Complete Data**: All articles with full metadata and content analysis
  * **Hub Articles**: Filtered view of hub-only and hub-project articles
  * **Content Summary**: Statistics and summaries of content types, metadata, and programming languages
* Apply clean table formatting with dark blue headers for easy filtering and sorting

When run as a separate step, it reads CONTENT_FILE and writes CONTENT_OUTPUT_FILE
