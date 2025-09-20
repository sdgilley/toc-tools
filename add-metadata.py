#!/usr/bin/env python3
"""
This script reads a CSV file containing file paths, opens each file,
and extracts metadata values for ms.author, description, and pivot from the front matter.
It then adds these metadata columns to the CSV and exports the enhanced data.

The script creates:
1. Main CSV file with comma-separated pivot_groups column

Optional: Merges Notes, NextGen?, and NextGen TOC columns from existing Excel file if MERGE_EXISTING and EXISTING_EXCEL_FILE is set.
Optional: Merges engagement metrics if MERGE_ENGAGEMENT and ENGAGEMENT_FILE is set.

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
    # Check if debug mode is enabled
    DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')
    
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
    

    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return
    
    print(f"Reading CSV file: {input_path}")
    if DEBUG:
        print(f"Base path for files: {base_path}")
    
    # Load pivot mapping
    pivot_mapping = load_pivot_mapping(pivot_map_file)
    if pivot_mapping:
        if DEBUG:
            print(f"Loaded {len(pivot_mapping)} pivot groups from: {pivot_map_file}")
    else:
        if DEBUG:
            print("No pivot mapping loaded")
    
    # Get configurable metadata fields from environment
    metadata_fields_config = os.getenv("METADATA_FIELDS", "ms.author,ms.topic,ms.service,description")
    metadata_fields = [field.strip() for field in metadata_fields_config.split(',')]
    
    # Check if zone_pivot_groups is in metadata fields - if so, enable pivot processing
    has_pivot_field = 'zone_pivot_groups' in metadata_fields
    
    metadata_flags_config = os.getenv("METADATA_FLAGS", "ms.custom:hub-only")
    metadata_flags = {}
    for field_config in metadata_flags_config.split(','):
        if ':' in field_config:
            field, flag_name = field_config.strip().split(':', 1)
            metadata_flags[field.strip()] = flag_name.strip()
    
    if DEBUG:
        print(f"Configured metadata fields: {metadata_fields}")
        print(f"Pivot processing enabled: {has_pivot_field}")
        print(f"Configured metadata flags: {metadata_flags}")
    
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    # Add new columns for metadata dynamically
    for field in metadata_fields:
        df[field] = ""
    
    # Add pivot-related columns only if zone_pivot_groups is in metadata fields
    if has_pivot_field:
        df['pivot_id'] = ""
        df['has_pivots'] = False
        df['pivot_groups'] = ""
    
    # Add metadata flag columns
    for flag_name in metadata_flags.values():
        df[flag_name] = False
    
    # Add system columns
    df['file_found'] = False
    

    
    # Process each row
    total_rows = len(df)
    processed_files = 0
    found_files = 0
    
    for index, row in df.iterrows():
        href = row.get('Href', '')
        
        if DEBUG and index % 50 == 0:  # Progress indicator
            print(f"Processing row {index + 1}/{total_rows}")
        
        # Resolve the file path
        file_path = resolve_file_path(href, base_path)
        
        if file_path:
            df.at[index, 'file_found'] = True
            found_files += 1
            
            # Extract metadata from the file
            metadata = extract_front_matter(file_path)
            
            # Extract configured metadata fields
            for field in metadata_fields:
                if field in metadata:
                    df.at[index, field] = metadata[field]
            
            # Handle pivot groups (only if zone_pivot_groups is in metadata fields)
            if has_pivot_field:
                pivot_group_ids = None
                if 'zone_pivot_groups' in metadata:
                    df.at[index, 'pivot_id'] = metadata['zone_pivot_groups']
                    pivot_group_ids = metadata['zone_pivot_groups']
                
                # Set pivot group data (always use comma-separated for main file)
                if pivot_group_ids:
                    pivot_groups = resolve_pivot_groups(pivot_group_ids, pivot_mapping)
                    
                    # Set has_pivots flag
                    df.at[index, 'has_pivots'] = True
                    
                    # Always set the comma-separated column for main file
                    df.at[index, 'pivot_groups'] = ', '.join(pivot_groups) if pivot_groups else ""
                

            
            # Handle metadata fields with flag logic
            for field_name, flag_name in metadata_flags.items():
                if field_name in metadata:
                    flag_found = False
                    custom_data = metadata[field_name]
                    
                    if isinstance(custom_data, str):
                        # If field is a string, check if it contains the flag
                        flag_found = flag_name in custom_data.lower()
                    elif isinstance(custom_data, list):
                        # If field is a list, check if any item contains the flag
                        flag_found = any(flag_name in str(item).lower() for item in custom_data)
                    elif isinstance(custom_data, dict):
                        # If field is a dict, check if any value contains the flag
                        flag_found = any(flag_name in str(value).lower() for value in custom_data.values())
                    
                    # Set the flag
                    df.at[index, flag_name] = flag_found
            
            processed_files += 1
    
    # Merge existing Excel file data if available and enabled
    merge_existing = os.getenv("MERGE_EXISTING", "False").lower() in ('true', '1', 'yes')
    existing_excel_file = os.getenv("EXISTING_EXCEL_FILE")
    
    if DEBUG:
        print(f"Debug: MERGE_EXISTING = {merge_existing}")
        print(f"Debug: EXISTING_EXCEL_FILE = '{existing_excel_file}'")
    
    if merge_existing and existing_excel_file:
        # Strip quotes and clean the path
        existing_excel_file = existing_excel_file.strip('"\'')
        if DEBUG:
            print(f"Debug: Cleaned EXISTING_EXCEL_FILE = '{existing_excel_file}'")
            print(f"Debug: File exists? {os.path.exists(existing_excel_file)}")
    
    if merge_existing and existing_excel_file and os.path.exists(existing_excel_file) and openpyxl:
        try:
            print(f"Merging NextGen data from existing Excel file: {existing_excel_file}")
            
            # Read the data sheet from the existing Excel file
            tab_name = os.getenv('EXISTING_FILE_TAB_NAME')
            if DEBUG:
                print(f"[DEBUG] EXISTING_EXCEL_FILE: {existing_excel_file}")
                print(f"[DEBUG] EXISTING_FILE_TAB_NAME: {tab_name}")
            if tab_name:
                if DEBUG:
                    print(f"[DEBUG] Using tab name from env: {tab_name}")
            else:
                if DEBUG:
                    print("[DEBUG] No tab name specified in env, using default sheet 'Complete Data'.")
                tab_name = 'Current Docs'
            try:
                df_existing = pd.read_excel(existing_excel_file, sheet_name=tab_name, engine='openpyxl')
                if DEBUG:
                    print(f"[DEBUG] Successfully loaded tab '{tab_name}' from Excel file.")
            except Exception as e:
                if DEBUG:
                    print(f"[DEBUG] WARNING: Could not open tab '{tab_name}' in existing Excel file: {e}")
                    print("[DEBUG] Falling back to first sheet.")
                try:
                    df_existing = pd.read_excel(existing_excel_file, sheet_name=0, engine='openpyxl')
                    if DEBUG:
                        print(f"[DEBUG] Successfully loaded first sheet from Excel file.")
                except Exception as e2:
                    print(f"[DEBUG] ERROR: Could not open any sheet in existing Excel file: {e2}")
                    df_existing = None
            if df_existing is not None and DEBUG:
                print(f"[DEBUG] Columns found in loaded sheet: {list(df_existing.columns)}")
            
            # Get merge columns from environment variable
            available_cols = list(df_existing.columns)
            if DEBUG:
                print(f"Available columns in existing file: {available_cols}")
            
            # Define columns we want to keep from environment variable
            merge_columns_config = os.getenv("MERGE_COLUMNS", "URL,Notes,NextGen?,NextGen TOC")
            desired_columns = [col.strip() for col in merge_columns_config.split(',')]
            merge_columns = [col for col in desired_columns if col in available_cols]
            
            key_column = desired_columns[0] if desired_columns else 'URL'  # First column is the key
            if key_column in merge_columns and len(merge_columns) > 1:  # Key column + at least one other column
                # Select columns and remove duplicates in one step
                df_existing = df_existing[merge_columns].drop_duplicates(subset=[key_column], keep='first')
                print(f"Merging data from existing Excel file - found {len(df_existing)} URLs with {', '.join(merge_columns[1:])} columns")
                if DEBUG:
                    print(f"Keeping columns for merge: {merge_columns}")
                    print(f"Existing Excel file after deduplication: {len(df_existing)} unique URLs")
                    print(f"Current data has {len(df)} rows")
                
                # Drop any existing merge columns (except key column) to avoid conflicts during merge
                key_column = desired_columns[0] if desired_columns else 'URL'  # First column is the key
                columns_to_drop = [col for col in desired_columns[1:] if col in df.columns]  # Skip key column
                if columns_to_drop and DEBUG:
                    df = df.drop(columns=columns_to_drop)
                    print(f"Dropped existing columns from current data: {columns_to_drop}")
                elif columns_to_drop:
                    df = df.drop(columns=columns_to_drop)
                
                # Perform direct merge on key column (no normalization needed)
                before_merge = len(df)
                df = df.merge(df_existing, how="left", on=key_column)
                after_merge = len(df)
                
                if DEBUG:
                    print(f"NextGen merge complete. Rows before: {before_merge}, after: {after_merge}")
                
                # Show sample of merged data
                try:
                    merged_data_summary = []
                    sample_cols = [key_column] + [col for col in merge_columns[1:] if col in df.columns]
                    
                    for col in merge_columns[1:]:  # Skip key column
                        if col in df.columns:
                            count = df[col].notna().sum()
                            merged_data_summary.append(f"{col}: {count} URLs")
                            if DEBUG:
                                print(f"Found {col} data for {count} URLs")
                    
                    if len(sample_cols) > 1 and DEBUG:
                        print(f"\nSample of merged data:")
                        # Show sample with non-null values
                        sample_filter = df[merge_columns[1:]].notna().any(axis=1)
                        if sample_filter.any():
                            sample = df[sample_filter][sample_cols].head()
                            print(sample)
                        else:
                            print("No non-null values found in merged columns")
                
                    # Reorder columns to put merged columns early
                    special_columns = [col for col in merge_columns[1:] if col in df.columns]  # Skip key column
                    if special_columns:
                        base_columns = ['Parent Path', 'Name', 'filename', key_column]
                        other_columns = [col for col in df.columns if col not in base_columns + special_columns]
                        final_column_order = base_columns + special_columns + other_columns
                        df = df[final_column_order]
                        if DEBUG:
                            print(f"Reordered columns with {', '.join(special_columns)} in early positions")
                            
                except Exception as sample_error:
                    if DEBUG:
                        print(f"Error displaying sample: {sample_error}")
                        print(f"Available columns after merge: {list(df.columns)}")
            else:
                print(f"Warning: No mergeable columns found in existing Excel file")
                if DEBUG:
                    print(f"Available columns: {available_cols}")
                    print(f"Looking for configured merge columns: {', '.join(desired_columns)}")
                    print(f"Key column '{key_column}' found: {key_column in available_cols}")
                    for col in desired_columns[1:]:  # Skip key column
                        print(f"'{col}' found: {col in available_cols}")
                
        except Exception as e:
            print(f"Error reading existing Excel file: {e}")
    elif not merge_existing and existing_excel_file:
        if DEBUG:
            print("Skipping existing Excel file merge (MERGE_EXISTING=False)")
    elif existing_excel_file and not os.path.exists(existing_excel_file):
        print(f"Warning: Existing Excel file not found: {existing_excel_file}")
    elif existing_excel_file and not openpyxl:
        print("Warning: openpyxl not available for reading Excel files")

    # Save the main enhanced CSV (always with comma-separated pivot_groups)
    df.to_csv(output_path, index=False)
    

    
    print(f"\nProcessing complete!")
    print(f"Total rows: {total_rows}")
    print(f"Files found: {found_files}")
    print(f"Files processed: {processed_files}")

    print(f"Main CSV saved to: {output_path}")
    
    # Show statistics for configured metadata fields
    print(f"\nMetadata Statistics:")
    
    # Statistics for regular metadata fields
    for field in metadata_fields:
        if field in df.columns:
            count = len(df[df[field].notna() & (df[field] != '')])
            print(f"Files with {field}: {count}")
    
    # Statistics for pivot fields (only if zone_pivot_groups is in metadata fields)
    if has_pivot_field and 'pivot_id' in df.columns:
        pivots = df[df['pivot_id'] != '']['pivot_id'].value_counts()
        print(f"Files with pivot_id: {len(df[df['pivot_id'] != ''])}")
        print(f"Files with has_pivots: {len(df[df['has_pivots'] == True])}")
        print(f"Files with pivot groups: {len(df[df['pivot_groups'] != ''])}")
    else:
        pivots = pd.Series(dtype=object)  # Empty series for debug section
    
    # Statistics for metadata flags
    for flag_name in metadata_flags.values():
        if flag_name in df.columns:
            count = len(df[df[flag_name] == True])
            print(f"Files with {flag_name}: {count}")
    
    if DEBUG:
        # Show detailed breakdowns for first few metadata fields
        for field in metadata_fields[:3]:  # Limit to first 3 to avoid too much output
            if field in df.columns:
                field_values = df[df[field].notna() & (df[field] != '')][field].value_counts()
                if len(field_values) > 0:
                    print(f"\nTop 5 {field} values:")
                    for value, count in field_values.head().items():
                        print(f"  {value}: {count} files")
            
        if has_pivot_field and len(pivots) > 0:
            print(f"\nPivot group IDs found:")
            for pivot, count in pivots.head(10).items():
                print(f"  {pivot}: {count} files")
        
        # Show resolved pivot group names from comma-separated column (only if pivot columns exist)
        if has_pivot_field and 'pivot_groups' in df.columns:
            pivot_group_names = df[df['pivot_groups'] != '']['pivot_groups'].value_counts()
            if len(pivot_group_names) > 0:
                print(f"\nResolved pivot group names:")
                for group_name, count in pivot_group_names.head(10).items():
                    print(f"  {group_name}: {count} files")
    
    return df  # Return main dataframe only
    


def create_excel_analysis(csv_file_path=None, output_file_name=None):
    """
    Create an Excel file with multiple tabs for analysis.
    
    Args:
        csv_file_path (str): Path to the CSV file with content analysis data.
                           If None, looks for toc_with_content.csv in script directory.
        output_file_name (str): Base name for output file. Excel extension will be added.
                              If None, uses "toc_analysis.xlsx"
    """
    # Check if debug mode is enabled
    DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')
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
    merge_engagement = os.getenv("MERGE_ENGAGEMENT", "False").lower() in ('true', '1', 'yes')
    engagement_file = os.getenv("ENGAGEMENT_FILE")
    if DEBUG:
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
                    if DEBUG:
                        print(f"Converted {col} to numeric format (removed commas and %)")
            
            if DEBUG:
                print("Normalizing engagement URLs...")
            df_engage["url_match"] = df_engage["Url"].apply(normalize_url)
            if DEBUG:
                print("\nFirst 5 engagement URLs and their normalized versions:")
                print(df_engage[["Url", "url_match"]].head())
        except Exception as e:
            print(f"Warning: Failed to read engagement file: {e}")
            df_engage = None
            
        if df_engage is not None:
            if "URL" in df.columns:
                if DEBUG:
                    print("\nNormalizing main DataFrame URLs...")
                df["url_match"] = df["URL"].apply(normalize_url)
                if DEBUG:
                    print("\nFirst 5 TOC URLs and their normalized versions:")
                    print(df[["URL", "url_match"]].head())
                    print("\nAttempting merge on 'url_match' column...")
                before_merge = len(df)
                
                # Debug: Show some stats before merge
                if DEBUG:
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
                
                engagement_matches = df['PageViews'].notna().sum()
                print(f"Engagement data merged: {engagement_matches} URLs matched")
                if DEBUG:
                    print(f"Merge complete. Rows before: {before_merge}, after: {after_merge}")

                # Drop the temporary url_match column as it's no longer needed
                df = df.drop(columns=["url_match"])
                
                # Debug: Show results
                if DEBUG:
                    print("\nSample of merged data:")
                    print(df[['URL', 'PageViews']].head())
            else:
                print("Main DataFrame missing 'URL' column!")
        else:
            if DEBUG:
                print("No engagement data available to merge")
        if DEBUG:
            print(df.head(10))
    
    # Check for pivot columns file
    df_pivots = None
    # pivot_file_path = csv_file_path.replace('.csv', '-pivots.csv')
    # if os.path.exists(pivot_file_path):
    #     print(f"Reading pivot columns file: {pivot_file_path}")
    #     df_pivots = pd.read_csv(pivot_file_path)
    
    
    # Reorder columns to ensure merged columns are in early positions
    merge_columns_config = os.getenv("MERGE_COLUMNS", "URL,Notes,NextGen?,NextGen TOC")
    desired_merge_columns = [col.strip() for col in merge_columns_config.split(',')]
    key_column = desired_merge_columns[0] if desired_merge_columns else 'URL'
    
    special_columns = []
    for col in desired_merge_columns[1:]:  # Skip key column
        if col in df.columns:
            special_columns.append(col)
    
    if special_columns:
        # Define desired column order
        base_columns = ['Parent Path', 'Name', 'filename', key_column]  # First 4 columns (A-D)
        
        # Get all other columns except the base ones and special columns
        other_columns = [col for col in df.columns if col not in base_columns + special_columns]
        
        # Create final column order: base + special + others
        final_column_order = base_columns + special_columns + other_columns
        
        # Only include columns that actually exist in the dataframe
        final_column_order = [col for col in final_column_order if col in df.columns]
        
        # Reorder the dataframe
        df = df[final_column_order]
        if DEBUG:
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
    data_sheets = ['Complete Data']
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
                if DEBUG:
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
                    if DEBUG:
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
    # if df_pivots is not None:
    #     print(f"Tab 3: Pivot Columns ({len(df_pivots)} rows with individual pivot boolean columns)")
    #     print(f"Tab 4: Content Summary with statistics tables")
    # else:
    print(f"Tab 2: Content Summary with statistics tables")
    
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
