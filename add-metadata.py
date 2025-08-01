#!/usr/bin/env python3
"""
This script reads a CSV file containing file paths, opens each file,
and extracts metadata values for ms.author, description, and pivot from the front matter.
It then adds these metadata columns to the CSV and exports the enhanced data.

The script creates:
1. Main CSV file with comma-separated pivot_groups column
2. If pivot groups exist: Additional "-pivots" CSV file with individual boolean columns for each pivot group

Usage:
    python add-metadata.py
"""

import pandas as pd
import os
import dotenv
import sys
from pathlib import Path
from utils.file_utils import extract_front_matter, resolve_file_path, load_pivot_mapping, resolve_pivot_groups

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
    df['description'] = ""
    df['pivot'] = ""
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
        
            if 'description' in metadata:
                df.at[index, 'description'] = metadata['description']
            
            # Handle pivot groups
            pivot_group_ids = None
            if 'zone_pivot_groups' in metadata:
                df.at[index, 'pivot'] = metadata['zone_pivot_groups']
                pivot_group_ids = metadata['zone_pivot_groups']
            elif 'pivot' in metadata:
                df.at[index, 'pivot'] = metadata['pivot']
                pivot_group_ids = metadata['pivot']
            
            # Set pivot group data (always use comma-separated for main file)
            if pivot_group_ids:
                pivot_groups = resolve_pivot_groups(pivot_group_ids, pivot_mapping)
                
                # Always set the comma-separated column for main file
                df.at[index, 'pivot_groups'] = ', '.join(pivot_groups) if pivot_groups else ""
                
                # Track discovered pivot groups for potential pivot file
                for pivot_group in pivot_groups:
                    discovered_pivot_groups.add(pivot_group)
            
            # Check for hub-only in custom metadata
            if 'custom' in metadata:
                custom_data = metadata['custom']
                if isinstance(custom_data, str):
                    # If custom is a string, check if it contains 'hub-only'
                    df.at[index, 'hub-only'] = 'hub-only' in custom_data.lower()
                elif isinstance(custom_data, list):
                    # If custom is a list, check if any item contains 'hub-only'
                    df.at[index, 'hub-only'] = any('hub-only' in str(item).lower() for item in custom_data)
                elif isinstance(custom_data, dict):
                    # If custom is a dict, check if any value contains 'hub-only'
                    df.at[index, 'hub-only'] = any('hub-only' in str(value).lower() for value in custom_data.values())
            
            processed_files += 1
    
    # Save the main enhanced CSV (always with comma-separated pivot_groups)
    df.to_csv(output_path, index=False)
    
    # Create pivot columns file if we discovered any pivot groups
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
    pivots = df[df['pivot'] != '']['pivot'].value_counts()
    
    print(f"\nMetadata Statistics:")
    print(f"Files with ms.author: {len(df[df['ms.author'] != ''])}")
    print(f"Files with ms.topic: {len(df[df['ms.topic'] != ''])}")
    print(f"Files with description: {len(df[df['description'] != ''])}")
    print(f"Files with pivot: {len(df[df['pivot'] != ''])}")
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
    
    if len(pivots) > 0:
        print(f"\nPivot groups found:")
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

if __name__ == "__main__":
    add_metadata_to_csv()
