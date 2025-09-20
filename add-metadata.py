#!/usr/bin/env python3
"""
This script reads a CSV file containing file paths, opens each file,
and extracts metadata values for ms.author, description, and pivot from the front matter.
It then adds these metadata columns to the CSV and exports the enhanced data.

The script creates:
1. Main CSV file with comma-separated pivot_groups column
2. If pivot groups exist: Additional "-pivots" CSV file with individual boolean columns for each pivot group

Optional: Merges Notes, NextGen?, and NextGen TOC columns from existing Excel file if EXISTING_EXCEL_FILE is set.
Optional: Merges engagement metrics if MERGE_ENGAGEMENT=1 and ENGAGEMENT_FILE is set.

Usage:
    python add-metadata.py
"""

import pandas as pd
import os
import dotenv
import sys
from pathlib import Path
from utils.file_utils import extract_front_matter, resolve_file_path, load_pivot_mapping, resolve_pivot_groups
from utils.url_normalizer import normalize_url
try:
    import openpyxl
except ImportError:
    openpyxl = None

# Load environment variables from .env file
dotenv.load_dotenv()

def add_metadata_to_csv():
    """
    Main function to read CSV, extract metadata, and create enhanced CSV.
    """
    # Get configuration from environment variables
    input_file = os.getenv("METADATA_FILE", "toc.csv")  # Use the existing output file as input
    base_path = os.getenv("BASE_PATH")  # Base path where the markdown files are located
    output_file = os.getenv("METADATA_OUTPUT_FILE", "toc_with_metadata.csv")
    pivot_map_file = os.getenv("PIVOT_MAP_FILE")  # Path to zone-pivot-groups.yml
    
    if not base_path:
        print("Error: BASE_PATH environment variable not set. Please set it to the root directory of your documentation.")
        return
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)
    
    # Create pivot file name by adding "-pivots" before the extension
    base_name, ext = os.path.splitext(output_file)
    pivot_output_file = f"{base_name}-pivots{ext}"
    pivot_output_path = os.path.join(script_dir, pivot_output_file)
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return
    
    print(f"Reading CSV file: {input_path}")
    print(f"Base path for files: {base_path}")
    
    # Load pivot mapping
    pivot_mapping = load_pivot_mapping(pivot_map_file)
    if pivot_mapping:
        print(f"Loaded {len(pivot_mapping)} pivot groups from: {pivot_map_file}")
    else:
        print("No pivot mapping loaded")
    
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    # Add new columns for metadata
    df['ms.author'] = ""
    df['ms.topic'] = ""
    df['ms.service'] = ""
    df['description'] = ""
    df['pivot_id'] = ""
    df['has_pivots'] = False
    df['pivot_groups'] = ""
    df['hub-only'] = False
    df['file_found'] = False
    
    # Track pivot groups as we discover them
    discovered_pivot_groups = set()
    
    # Process each row
    total_rows = len(df)
    processed_files = 0
    found_files = 0
    
    for index, row in df.iterrows():
        href = row.get('Href', '')
        
        if index % 50 == 0:  # Progress indicator
            print(f"Processing row {index + 1}/{total_rows}")
        
        # Resolve the file path
        file_path = resolve_file_path(href, base_path)
        
        if file_path:
            df.at[index, 'file_found'] = True
            found_files += 1
            
            # Extract metadata from the file
            metadata = extract_front_matter(file_path)
            
            # Extract specific fields
            if 'ms.author' in metadata:
                df.at[index, 'ms.author'] = metadata['ms.author']
            
            if 'ms.topic' in metadata:
                df.at[index, 'ms.topic'] = metadata['ms.topic']

            if 'ms.service' in metadata:
                df.at[index, 'ms.service'] = metadata['ms.service']
        
            if 'description' in metadata:
                df.at[index, 'description'] = metadata['description']
            
            # Handle pivot groups
            pivot_group_ids = None
            if 'zone_pivot_groups' in metadata:
                df.at[index, 'pivot_id'] = metadata['zone_pivot_groups']
                pivot_group_ids = metadata['zone_pivot_groups']
            elif 'pivot' in metadata:
                df.at[index, 'pivot_id'] = metadata['pivot']
                pivot_group_ids = metadata['pivot']
            
            # Set pivot group data (always use comma-separated for main file)
            if pivot_group_ids:
                pivot_groups = resolve_pivot_groups(pivot_group_ids, pivot_mapping)
                
                # Set has_pivots flag
                df.at[index, 'has_pivots'] = True
                
                # Always set the comma-separated column for main file
                df.at[index, 'pivot_groups'] = ', '.join(pivot_groups) if pivot_groups else ""
                
                # Track discovered pivot groups for potential pivot file
                for pivot_group in pivot_groups:
                    discovered_pivot_groups.add(pivot_group)
            
            # Check for hub-only in ms.custom metadata
            hub_only_found = False
            
            # Check 'ms.custom' field
            if 'ms.custom' in metadata:
                custom_data = metadata['ms.custom']
                if isinstance(custom_data, str):
                    # If ms.custom is a string, check if it contains 'hub-only'
                    hub_only_found = 'hub-only' in custom_data.lower()
                elif isinstance(custom_data, list):
                    # If ms.custom is a list, check if any item contains 'hub-only'
                    hub_only_found = any('hub-only' in str(item).lower() for item in custom_data)
                elif isinstance(custom_data, dict):
                    # If ms.custom is a dict, check if any value contains 'hub-only'
                    hub_only_found = any('hub-only' in str(value).lower() for value in custom_data.values())
            
            # Set the hub-only flag
            df.at[index, 'hub-only'] = hub_only_found
            
            processed_files += 1
    
    # Merge existing Excel file data if available
    existing_excel_file = os.getenv("EXISTING_EXCEL_FILE")
    if existing_excel_file:
        # Strip quotes and clean the path
        existing_excel_file = existing_excel_file.strip('"\'')
        print(f"Debug: EXISTING_EXCEL_FILE = '{existing_excel_file}'")
        print(f"Debug: File exists? {os.path.exists(existing_excel_file)}")
    
    if existing_excel_file and os.path.exists(existing_excel_file) and openpyxl:
        try:
            print(f"Merging NextGen data from existing Excel file: {existing_excel_file}")
            
            # Read the 'Complete Data' sheet from the existing Excel file
            tab_name = os.getenv('EXISTING_FILE_TAB_NAME')
            print(f"[DEBUG] EXISTING_EXCEL_FILE: {existing_excel_file}")
            print(f"[DEBUG] EXISTING_FILE_TAB_NAME: {tab_name}")
            if tab_name:
                print(f"[DEBUG] Using tab name from env: {tab_name}")
            else:
                print("[DEBUG] No tab name specified in env, using default sheet 'Complete Data'.")
                tab_name = 'Current Docs'
            try:
                df_existing = pd.read_excel(existing_excel_file, sheet_name=tab_name, engine='openpyxl')
                print(f"[DEBUG] Successfully loaded tab '{tab_name}' from Excel file.")
            except Exception as e:
                print(f"[DEBUG] WARNING: Could not open tab '{tab_name}' in existing Excel file: {e}")
                print("[DEBUG] Falling back to first sheet.")
                try:
                    df_existing = pd.read_excel(existing_excel_file, sheet_name=0, engine='openpyxl')
                    print(f"[DEBUG] Successfully loaded first sheet from Excel file.")
                except Exception as e2:
                    print(f"[DEBUG] ERROR: Could not open any sheet in existing Excel file: {e2}")
                    df_existing = None
            if df_existing is not None:
                print(f"[DEBUG] Columns found in loaded sheet: {list(df_existing.columns)}")
            
            # Select only the columns we want to merge: URL + Notes + NextGen? + NextGen TOC
            available_cols = list(df_existing.columns)
            print(f"Available columns in existing file: {available_cols}")
            
            # Define columns we want to keep
            desired_columns = ['URL', 'Notes', 'NextGen?', 'NextGen TOC']
            merge_columns = [col for col in desired_columns if col in available_cols]
            
            if 'URL' in merge_columns and len(merge_columns) > 1:  # URL + at least one other column
                # Select columns and remove duplicates in one step
                df_existing = df_existing[merge_columns].drop_duplicates(subset=['URL'], keep='first')
                print(f"Keeping columns for merge: {merge_columns}")
                print(f"Existing Excel file after deduplication: {len(df_existing)} unique URLs")
                print(f"Current data has {len(df)} rows")
                
                # Drop any existing Notes/NextGen columns to avoid conflicts during merge
                columns_to_drop = [col for col in ['Notes', 'NextGen?', 'NextGen TOC'] if col in df.columns]
                if columns_to_drop:
                    df = df.drop(columns=columns_to_drop)
                    print(f"Dropped existing columns from current data: {columns_to_drop}")
                
                # Perform direct merge on URL column (no normalization needed)
                before_merge = len(df)
                df = df.merge(df_existing, how="left", on="URL")
                after_merge = len(df)
                
                print(f"NextGen merge complete. Rows before: {before_merge}, after: {after_merge}")
                
                # Show sample of merged data
                try:
                    merged_data_summary = []
                    sample_cols = ['URL'] + [col for col in merge_columns[1:] if col in df.columns]
                    
                    for col in merge_columns[1:]:  # Skip URL
                        if col in df.columns:
                            count = df[col].notna().sum()
                            merged_data_summary.append(f"{col}: {count} URLs")
                            print(f"Found {col} data for {count} URLs")
                    
                    if len(sample_cols) > 1:
                        print(f"\nSample of merged data:")
                        # Show sample with non-null values
                        sample_filter = df[merge_columns[1:]].notna().any(axis=1)
                        if sample_filter.any():
                            sample = df[sample_filter][sample_cols].head()
                            print(sample)
                        else:
                            print("No non-null values found in merged columns")
                
                    # Reorder columns to put Notes and NextGen columns early
                    special_columns = [col for col in merge_columns[1:] if col in df.columns]
                    if special_columns:
                        base_columns = ['Parent Path', 'Name', 'filename', 'URL']
                        other_columns = [col for col in df.columns if col not in base_columns + special_columns]
                        final_column_order = base_columns + special_columns + other_columns
                        df = df[final_column_order]
                        print(f"Reordered columns with {', '.join(special_columns)} in early positions")
                            
                except Exception as sample_error:
                    print(f"Error displaying sample: {sample_error}")
                    print(f"Available columns after merge: {list(df.columns)}")
            else:
                print(f"Warning: No mergeable columns found in existing Excel file")
                print(f"Available columns: {available_cols}")
                print(f"Looking for: URL (required) and any of: Notes, NextGen?, NextGen TOC")
                print(f"'URL' found: {'URL' in available_cols}")
                print(f"'Notes' found: {'Notes' in available_cols}")
                print(f"'NextGen?' found: {'NextGen?' in available_cols}")
                print(f"'NextGen TOC' found: {'NextGen TOC' in available_cols}")
                
        except Exception as e:
            print(f"Error reading existing Excel file: {e}")
    elif existing_excel_file and not os.path.exists(existing_excel_file):
        print(f"Warning: Existing Excel file not found: {existing_excel_file}")
    elif existing_excel_file and not openpyxl:
        print("Warning: openpyxl not available for reading Excel files")

    # Save the main enhanced CSV (always with comma-separated pivot_groups)
    df.to_csv(output_path, index=False)
    
    # Create pivot columns file if we discovered any pivot groups
    df_pivots = None
    if discovered_pivot_groups:
        print(f"Creating pivot columns file with {len(discovered_pivot_groups)} unique pivot groups...")
        
        # Create a copy of the dataframe for pivot columns
        df_pivots = df.copy()
        
        # Add individual boolean columns for each discovered pivot group
        for pivot_group in sorted(discovered_pivot_groups):
            # Create safe column name (replace hyphens with underscores)
            safe_column_name = f"pivot_{pivot_group.replace('-', '_')}"
            df_pivots[safe_column_name] = False
        
        # Process each row again to set the individual pivot columns
        for index, row in df_pivots.iterrows():
            pivot_groups_str = row.get('pivot_groups', '')
            if pivot_groups_str:
                # Split the comma-separated string back to individual groups
                pivot_groups = [pg.strip() for pg in pivot_groups_str.split(',')]
                
                # Set the corresponding boolean columns
                for pivot_group in pivot_groups:
                    safe_column_name = f"pivot_{pivot_group.replace('-', '_')}"
                    if safe_column_name in df_pivots.columns:
                        df_pivots.at[index, safe_column_name] = True
        
        # Save the pivot columns CSV
        df_pivots.to_csv(pivot_output_path, index=False)
        print(f"Pivot columns CSV saved to: {pivot_output_path}")
    
    print(f"\nProcessing complete!")
    print(f"Total rows: {total_rows}")
    print(f"Files found: {found_files}")
    print(f"Files processed: {processed_files}")
    if discovered_pivot_groups:
        print(f"Discovered {len(discovered_pivot_groups)} unique pivot groups")
    print(f"Main CSV saved to: {output_path}")
    
    # Show some statistics
    authors = df[df['ms.author'] != '']['ms.author'].value_counts()
    topics = df[df['ms.topic'] != '']['ms.topic'].value_counts()
    services = df[df['ms.service'] != '']['ms.service'].value_counts()
    pivots = df[df['pivot_id'] != '']['pivot_id'].value_counts()
    
    print(f"\nMetadata Statistics:")
    print(f"Files with ms.author: {len(df[df['ms.author'] != ''])}")
    print(f"Files with ms.topic: {len(df[df['ms.topic'] != ''])}")
    print(f"Files with ms.service: {len(df[df['ms.service'] != ''])}")
    print(f"Files with description: {len(df[df['description'] != ''])}")
    print(f"Files with pivot_id: {len(df[df['pivot_id'] != ''])}")
    print(f"Files with has_pivots: {len(df[df['has_pivots'] == True])}")
    print(f"Files with pivot groups: {len(df[df['pivot_groups'] != ''])}")
    print(f"Files with hub-only: {len(df[df['hub-only'] == True])}")
    
    if len(authors) > 0:
        print(f"\nTop 5 authors:")
        for author, count in authors.head().items():
            print(f"  {author}: {count} files")
    
    if len(topics) > 0:
        print(f"\nTop 5 topics:")
        for topic, count in topics.head().items():
            print(f"  {topic}: {count} files")

    if len(services) > 0:
        print(f"\nms.service:")
        for service, count in services.items():
            print(f"  {service}: {count} files")
            
    return df, df_pivots  # Return both dataframes for potential Excel export
    
    if len(pivots) > 0:
        print(f"\nPivot group IDs found:")
        for pivot, count in pivots.head(10).items():
            print(f"  {pivot}: {count} files")
    
    # Show resolved pivot group names from comma-separated column
    pivot_group_names = df[df['pivot_groups'] != '']['pivot_groups'].value_counts()
    if len(pivot_group_names) > 0:
        print(f"\nResolved pivot group names:")
        for group_name, count in pivot_group_names.head(10).items():
            print(f"  {group_name}: {count} files")
    
    # Show individual pivot group usage if we created a pivot file
    if discovered_pivot_groups:
        print(f"\nIndividual pivot group usage (in pivot columns file):")
        pivot_columns = [f"pivot_{pg.replace('-', '_')}" for pg in sorted(discovered_pivot_groups)]
        for col in pivot_columns[:10]:  # Show top 10
            # Count from the pivot_groups column
            pivot_name = col.replace('pivot_', '').replace('_', '-')
            count = sum(1 for _, row in df.iterrows() 
                       if row.get('pivot_groups', '') and pivot_name in row['pivot_groups'].split(', '))
            print(f"  {pivot_name}: {count} files")

def create_excel_analysis(csv_file_path=None, output_file_name=None):
    """
    Create an Excel file with multiple tabs for analysis.
    
    Args:
        csv_file_path (str): Path to the CSV file with content analysis data.
                           If None, looks for toc_with_content.csv in script directory.
        output_file_name (str): Base name for output file. Excel extension will be added.
                              If None, uses "toc_analysis.xlsx"
    """
    try:
        import openpyxl
        from openpyxl.utils.dataframe import dataframe_to_rows
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        print("Error: openpyxl is required for Excel export. Install with: pip install openpyxl")
        return
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determine input CSV file
    if csv_file_path is None:
        csv_file_path = os.path.join(script_dir, "toc_with_content.csv")
    
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file {csv_file_path} not found.")
        print("Make sure to run the complete analysis pipeline first.")
        return
    
    # Read the CSV file
    print(f"Reading CSV file: {csv_file_path}")
    df = pd.read_csv(csv_file_path)

    # URL normalization already imported at top of file

    # Merge engagement metrics if available and enabled
    merge_engagement = os.getenv("MERGE_ENGAGEMENT", "0") == "1"
    engagement_file = os.getenv("ENGAGEMENT_FILE")
    print(f"Debug: MERGE_ENGAGEMENT env var = {os.getenv('MERGE_ENGAGEMENT')}")
    print(f"Debug: merge_engagement = {merge_engagement}")
    print(f"Debug: ENGAGEMENT_FILE = {engagement_file}")
    if engagement_file:
        print(f"Debug: File exists? {os.path.exists(engagement_file)}")
    df_engage = None
    if merge_engagement and engagement_file and os.path.exists(engagement_file):
        try:
            print(f"Merging engagement metrics from: {engagement_file}")
            df_engage = pd.read_csv(engagement_file)
            # Only keep relevant columns
            engage_cols = ["Url", "PageViews", "PVMoM", "Visitors", "Engagement"]
            df_engage = df_engage[engage_cols]
            
            # Convert numeric columns from string format (remove commas, percentages and convert to numeric)
            numeric_cols = ["PageViews", "PVMoM", "Visitors"]
            for col in numeric_cols:
                if col in df_engage.columns:
                    # Remove commas and percentage signs, then convert to numeric
                    df_engage[col] = df_engage[col].astype(str).str.replace(',', '').str.replace('%', '')
                    df_engage[col] = pd.to_numeric(df_engage[col], errors='coerce')
                    print(f"Converted {col} to numeric format (removed commas and %)")
            
            print("Normalizing engagement URLs...")
            df_engage["url_match"] = df_engage["Url"].apply(normalize_url)
            print("\nFirst 5 engagement URLs and their normalized versions:")
            print(df_engage[["Url", "url_match"]].head())
        except Exception as e:
            print(f"Warning: Failed to read engagement file: {e}")
            df_engage = None
            
        if df_engage is not None:
            if "URL" in df.columns:
                print("\nNormalizing main DataFrame URLs...")
                df["url_match"] = df["URL"].apply(normalize_url)
                print("\nFirst 5 TOC URLs and their normalized versions:")
                print(df[["URL", "url_match"]].head())
                print("\nAttempting merge on 'url_match' column...")
                before_merge = len(df)
                
                # Debug: Show some stats before merge
                print(f"\nUnique normalized URLs in engagement data: {df_engage['url_match'].nunique()}")
                print(f"Unique normalized URLs in TOC data: {df['url_match'].nunique()}")
                print("\nSample of URLs that should match:")
                sample = df.merge(df_engage, left_on='url_match', right_on='url_match').head()
                if not sample.empty:
                    print(sample[['URL', 'Url', 'url_match']].head())
                else:
                    print("No matching URLs found!")
                
                # Perform the merge
                df = df.merge(df_engage.drop(columns=["Url"]), how="left", on="url_match")
                after_merge = len(df)
                print(f"\nMerge complete. Rows before: {before_merge}, after: {after_merge}")

                # Drop the temporary url_match column as it's no longer needed
                df = df.drop(columns=["url_match"])
                
                # Debug: Show results
                print("\nSample of merged data:")
                print(df[['URL', 'PageViews']].head())
            else:
                print("Main DataFrame missing 'URL' column!")
        else:
            print("No engagement data available to merge")
        print(df.head(10))
    
    # Check for pivot columns file
    df_pivots = None
    # pivot_file_path = csv_file_path.replace('.csv', '-pivots.csv')
    # if os.path.exists(pivot_file_path):
    #     print(f"Reading pivot columns file: {pivot_file_path}")
    #     df_pivots = pd.read_csv(pivot_file_path)
    
    
    # Reorder columns to ensure Notes and NextGen columns are in early positions
    special_columns = []
    for col in ['Notes', 'NextGen', 'NextGen?', 'NextGen TOC']:
        if col in df.columns:
            special_columns.append(col)
    
    if special_columns:
        # Define desired column order
        base_columns = ['Parent Path', 'Name', 'filename', 'URL']  # First 4 columns (A-D)
        
        # Get all other columns except the base ones and special columns
        other_columns = [col for col in df.columns if col not in base_columns + special_columns]
        
        # Create final column order: base + special + others
        final_column_order = base_columns + special_columns + other_columns
        
        # Only include columns that actually exist in the dataframe
        final_column_order = [col for col in final_column_order if col in df.columns]
        
        # Reorder the dataframe
        df = df[final_column_order]
        print(f"Reordered columns with {', '.join(special_columns)} in early positions")
    
    # Create Excel file path using output file name
    if output_file_name:
        # Remove extension if present and add .xlsx
        base_name = os.path.splitext(output_file_name)[0]
        excel_file_path = os.path.join(script_dir, f"{base_name}.xlsx")
    else:
        excel_file_path = os.path.join(script_dir, "toc_analysis.xlsx")
    
    # Create Excel writer
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        
        # Tab: Complete data
        print("Creating Tab: Complete Data")
        df.to_excel(writer, sheet_name='Complete Data', index=False)
        
        # Tab: Hub-only and hub-project articles
        print("Creating Tab: Hub Articles")
        # Handle pivot_groups column safely
        pivot_filter = False
        if 'pivot_groups' in df.columns:
            pivot_series = df['pivot_groups'].astype(str)
            pivot_filter = pivot_series.str.contains('hub-project', na=False)
        
        hub_filter = (df['hub-only'] == True) | pivot_filter
        hub_df = df[hub_filter]
        hub_df.to_excel(writer, sheet_name='Hub Articles', index=False)
        
        # # Tab: Pivot columns (if available)
        # if df_pivots is not None:
        #     print("Creating Tab: Pivot Columns")
        #     df_pivots.to_excel(writer, sheet_name='Pivot Columns', index=False)
        
        # Tab: Summary statistics
        summary_tab_name = 'Content Summary'
        print(f"Creating Tab: {summary_tab_name}")
        
        # Create summary data
        summary_data = []
        
        # Content type summaries
        if 'has_tabs' in df.columns:
            files_with_tabs = len(df[df['has_tabs'] == True])
            total_tabs = df['tab_count'].sum() if 'tab_count' in df.columns else 0
            summary_data.append(['Content Type', 'Files with Content', 'Total Instances'])
            summary_data.append(['Tabs', files_with_tabs, total_tabs])
        
        if 'has_images' in df.columns:
            files_with_images = len(df[df['has_images'] == True])
            total_images = df['image_count'].sum() if 'image_count' in df.columns else 0
            summary_data.append(['Images', files_with_images, total_images])
        
        if 'has_code_blocks' in df.columns:
            files_with_code_blocks = len(df[df['has_code_blocks'] == True])
            total_code_blocks = df['code_block_count'].sum() if 'code_block_count' in df.columns else 0
            summary_data.append(['Code Blocks', files_with_code_blocks, total_code_blocks])
        
        if 'has_code_refs' in df.columns:
            files_with_code_refs = len(df[df['has_code_refs'] == True])
            total_code_refs = df['code_ref_count'].sum() if 'code_ref_count' in df.columns else 0
            summary_data.append(['Code References', files_with_code_refs, total_code_refs])
        
        if 'portal_steps' in df.columns:
            files_with_portal_steps = len(df[df['portal_steps'] == True])
            summary_data.append(['Portal Steps', files_with_portal_steps, '-'])
        
        # Create summary DataFrame if we have data
        if len(summary_data) > 0:
            summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            summary_df.to_excel(writer, sheet_name=summary_tab_name, index=False, startrow=0)
        else:
            # Create an empty DataFrame with default columns
            summary_df = pd.DataFrame(columns=['Content Type', 'Files with Content', 'Total Instances'])
            summary_df.to_excel(writer, sheet_name=summary_tab_name, index=False, startrow=0)
        
        # Add metadata summary
        metadata_summary = []
        metadata_summary.append(['Metadata Type', 'Files with Metadata'])
        
        if 'ms.author' in df.columns:
            files_with_author = len(df[df['ms.author'].notna() & (df['ms.author'] != '')])
            metadata_summary.append(['Authors', files_with_author])
        
        if 'ms.topic' in df.columns:
            files_with_topic = len(df[df['ms.topic'].notna() & (df['ms.topic'] != '')])
            metadata_summary.append(['Topics', files_with_topic])
        
        if 'ms.service' in df.columns:
            files_with_service = len(df[df['ms.service'].notna() & (df['ms.service'] != '')])
            # Count unique services
            unique_services = df[df['ms.service'].notna() & (df['ms.service'] != '')]['ms.service'].nunique()
            metadata_summary.append(['Services', f"{files_with_service} files ({unique_services} unique)"])
            
            # Add a breakdown of services
            service_counts = df[df['ms.service'].notna() & (df['ms.service'] != '')]['ms.service'].value_counts()
            for service, count in service_counts.items():
                metadata_summary.append([f"  {service}", count])
        
        if 'description' in df.columns:
            files_with_description = len(df[df['description'] != ''])
            metadata_summary.append(['Descriptions', files_with_description])
        
        if 'has_pivots' in df.columns:
            files_with_pivots = len(df[df['has_pivots'] == True])
            metadata_summary.append(['Pivot Groups', files_with_pivots])
        
        if 'hub-only' in df.columns:
            files_hub_only = len(df[df['hub-only'] == True])
            metadata_summary.append(['Hub-Only', files_hub_only])
        
        # Add metadata summary to the same sheet
        metadata_df = pd.DataFrame(metadata_summary[1:], columns=metadata_summary[0])
        metadata_df.to_excel(writer, sheet_name=summary_tab_name, index=False, startrow=len(summary_df) + 3)
        
        # Add top programming languages if available
        if 'code_languages' in df.columns:
            all_languages = []
            for _, row in df.iterrows():
                if row['code_languages'] and pd.notna(row['code_languages']):
                    languages = [lang.strip() for lang in str(row['code_languages']).split(',')]
                    all_languages.extend(languages)
            
            if all_languages:
                from collections import Counter
                lang_counts = Counter(all_languages)
                
                lang_summary = [['Programming Language', 'File Count']]
                for lang, count in lang_counts.most_common(10):
                    if lang and lang != 'none':
                        lang_summary.append([lang, count])
                
                lang_df = pd.DataFrame(lang_summary[1:], columns=lang_summary[0])
                lang_df.to_excel(writer, sheet_name=summary_tab_name, index=False, 
                               startrow=len(summary_df) + len(metadata_df) + 6)
    
    # Format the Excel file
    wb = openpyxl.load_workbook(excel_file_path)
    
    # Convert data sheets to Excel tables (for filtering and sorting)
    data_sheets = ['Complete Data', 'Hub Articles']
    for sheet_name in data_sheets:
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            
            # Get the data range
            max_row = ws.max_row
            max_col = ws.max_column
            
            if max_row > 1 and max_col > 0:  # Only create table if there's data
                # Create table reference
                table_ref = f"A1:{ws.cell(max_row, max_col).coordinate}"
                
                # Create table
                from openpyxl.worksheet.table import Table, TableStyleInfo
                table = Table(displayName=f"Table_{sheet_name.replace(' ', '')}", ref=table_ref)
                
                # Add a clean table style with dark blue headers
                style = TableStyleInfo(
                    name="TableStyleMedium16",  # Dark blue headers with clean white rows
                    showFirstColumn=False,
                    showLastColumn=False, 
                    showRowStripes=False,  # No row stripes for cleaner look
                    showColumnStripes=False  # No column stripes for cleaner look
                )
                table.tableStyleInfo = style
                
                # Add the table to the worksheet
                ws.add_table(table)
                print(f"Added Excel table formatting to '{sheet_name}' sheet")

                # Find URL column index
                header_row = ws[1]
                url_col_index = None
                for cell in header_row:
                    if cell.value == "URL":
                        url_col_index = cell.column
                        break
                
                if url_col_index:
                    # Check for special columns (Notes, NextGen, NextGen?) after URL
                    special_col_index = None
                    special_columns_to_check = ['Notes', 'NextGen', 'NextGen?']
                    
                    # Find the last special column after URL
                    for col_idx in range(url_col_index + 1, max_col + 1):
                        cell_value = ws.cell(row=1, column=col_idx).value
                        if cell_value in special_columns_to_check:
                            special_col_index = col_idx
                    
                    # Insert new column after the last special column if it exists, otherwise after URL
                    insert_position = special_col_index + 1 if special_col_index else url_col_index + 1
                    ws.insert_cols(insert_position)
                    
                    # Add header for link column
                    link_cell = ws.cell(row=1, column=insert_position)
                    link_cell.value = "Link"
                    
                    # Add hyperlink formula to each row
                    for row in range(2, max_row + 1):
                        formula_cell = ws.cell(row=row, column=insert_position)
                        url_cell = ws.cell(row=row, column=url_col_index).coordinate
                        formula_cell.value = f'=HYPERLINK({url_cell},"🔗")'
                    
                    # Hide URL column
                    col_letter = ws.cell(row=1, column=url_col_index).column_letter
                    ws.column_dimensions[col_letter].hidden = True
                    
                    # Adjust table range to include new column
                    table.ref = f"A1:{ws.cell(max_row, max_col + 1).coordinate}"
                    print(f"Added hyperlink column and hid URL column in '{sheet_name}' sheet")
    
    # Format Summary tab (Content Summary)
    if summary_tab_name in wb.sheetnames:
        ws = wb[summary_tab_name]
        
        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        # Style first table headers
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Style second table headers (metadata)
        metadata_start_row = len(summary_df) + 4
        for cell in ws[metadata_start_row]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
        
        # Style third table headers (languages) if it exists
        if 'all_languages' in locals() and len(all_languages) > 0:
            lang_start_row = len(summary_df) + len(metadata_df) + 7
            for cell in ws[lang_start_row]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(excel_file_path)
    
    print(f"\nExcel analysis file created: {excel_file_path}")
    print(f"Tab 1: Complete Data ({len(df)} rows)")
    print(f"Tab 2: Hub Articles ({len(hub_df)} rows)")
    # if df_pivots is not None:
    #     print(f"Tab 3: Pivot Columns ({len(df_pivots)} rows with individual pivot boolean columns)")
    #     print(f"Tab 4: Content Summary with statistics tables")
    # else:
    print(f"Tab 3: Content Summary with statistics tables")
    
    return excel_file_path

if __name__ == "__main__":
    import sys
    
    # Check if user wants to create Excel analysis
    if len(sys.argv) > 1 and sys.argv[1] == "--excel":
        # If a CSV file path is provided as second argument, use it
        csv_path = sys.argv[2] if len(sys.argv) > 2 else None
        create_excel_analysis(csv_path)
    else:
        add_metadata_to_csv()
