#!/usr/bin/env python3
"""
This script reads a CSV file containing file paths, opens each file,
and analyzes the content to extract information about tabs and images.
It then adds these content analysis columns to the CSV and exports the enhanced data.

The script creates:
1. Main CSV file with content analysis columns (tabs, images)

Usage:
    python add-content-analysis.py
"""

import pandas as pd
import os
import re
import dotenv
from pathlib import Path
from utils.file_utils import resolve_file_path, read_file_content

# Load environment variables from .env file
dotenv.load_dotenv()

def analyze_content(file_path):
    """
    Analyze markdown file content for tabs and images.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        dict: Dictionary containing content analysis results
    """
    try:
        content = read_file_content(file_path)
        if not content:
            # Return empty analysis if file couldn't be read
            return {
                'has_tabs': False,
                'tab_count': 0,
                'tab_formats': [],
                'has_images': False,
                'image_count': 0,
                'portal_steps': False,
                'has_code_blocks': False,
                'code_block_count': 0,
                'code_languages': [],
                'has_code_refs': False,
                'code_ref_count': 0,
                'Contains_link': False,
                'Contains_link_with_param': False
            }
        
        analysis = {
            'has_tabs': False,
            'tab_count': 0,
            'tab_formats': [],
            'has_images': False,
            'image_count': 0,
            'portal_steps': False,
            'has_code_blocks': False,
            'code_block_count': 0,
            'code_languages': [],
            'has_code_refs': False,
            'code_ref_count': 0,
            'Contains_link': False,
            'Contains_link_with_param': False
        }
        
        # Look for tab formats: #tab/xxx
        tab_pattern = r'#tab/([^)\s]+)'
        tab_matches = re.findall(tab_pattern, content, re.IGNORECASE)
        if tab_matches:
            analysis['has_tabs'] = True
            analysis['tab_count'] = len(tab_matches)
            analysis['tab_formats'] = list(set(tab_matches))  # Remove duplicates
        
        # Look for image formats: :::image
        image_pattern = r':::image\s+(?:type="([^"]+)"\s+)?source="([^"]+)"'
        image_matches = re.findall(image_pattern, content, re.IGNORECASE)
        if image_matches:
            analysis['has_images'] = True
            analysis['image_count'] = len(image_matches)
        
        # Also look for standard markdown images: ![alt](src)
        md_image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        md_image_matches = re.findall(md_image_pattern, content)
        if md_image_matches:
            if not analysis['has_images']:
                analysis['has_images'] = True
                analysis['image_count'] = 0
            analysis['image_count'] += len(md_image_matches)
        
        # Look for code blocks: ``` or ~~~
        # Pattern to match fenced code blocks with optional language specification
        code_block_pattern = r'^(?:```|~~~)([^\n\r]*)'
        code_block_matches = re.findall(code_block_pattern, content, re.MULTILINE)
        if code_block_matches:
            analysis['has_code_blocks'] = True
            analysis['code_block_count'] = len(code_block_matches)
            # Extract language specifications
            for lang_spec in code_block_matches:
                lang_spec = lang_spec.strip()
                if lang_spec:  # If there's a language specified
                    # Split by whitespace and take first part (language)
                    lang = lang_spec.split()[0].lower()
                    if lang and lang not in analysis['code_languages']:
                        analysis['code_languages'].append(lang)
                else:
                    # Code block without language specification
                    if 'none' not in analysis['code_languages']:
                        analysis['code_languages'].append('none')
        
        # Look for code references: :::code
        code_ref_pattern = r':::code[^\n]*'
        code_ref_matches = re.findall(code_ref_pattern, content, re.IGNORECASE)
        if code_ref_matches:
            analysis['has_code_refs'] = True
            analysis['code_ref_count'] = len(code_ref_matches)
        
        # Look for portal steps: numbered lines like "1. Step one", "2. Step two"
        # Pattern looks for lines that start with a number followed by a period and space
        step_pattern = r'^\s*\d+\.\s+'
        lines = content.split('\n')
        numbered_lines = [line for line in lines if re.match(step_pattern, line)]
        
        # Consider it portal steps if we have at least 2 consecutive numbered items
        if len(numbered_lines) >= 2:
            # Check if we have a sequence starting from 1
            first_numbers = []
            for line in numbered_lines[:5]:  # Check first 5 to see if we have 1, 2, 3...
                match = re.match(r'^\s*(\d+)\.\s+', line)
                if match:
                    first_numbers.append(int(match.group(1)))
            
            # If we start with 1 and have at least 2 consecutive numbers, it's likely portal steps
            if first_numbers and first_numbers[0] == 1 and len(first_numbers) >= 2:
                analysis['portal_steps'] = True
        
        # Strip .md from URLs before link checks
        content_for_link = content.replace('.md', '')
        # Check for links to https://ai.azure.com (no parameters)
        contains_link_no_param = bool(re.search(r'https://ai\.azure\.com\b(?![/?]\?)', content_for_link))
        # Check for links to https://ai.azure.com?cid=learnDocs or https://ai.azure.com/?cid=learnDocs
        contains_link_with_param = bool(re.search(r'https://ai\.azure\.com/?\?cid=learnDocs', content_for_link))
        analysis['contains_link_no_param'] = contains_link_no_param
        analysis['Contains_link_with_param'] = contains_link_with_param

        return analysis
        
    except Exception as e:
        # Only show error details in debug mode
        DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')
        if DEBUG:
            print(f"Error analyzing file {file_path}: {e}")
        return {
            'has_tabs': False,
            'tab_count': 0,
            'tab_formats': [],
            'has_images': False,
            'image_count': 0,
            'portal_steps': False,
            'has_code_blocks': False,
            'code_block_count': 0,
            'code_languages': [],
            'has_code_refs': False,
            'code_ref_count': 0,
            'Contains_link': False,
            'Contains_link_with_param': False
        }

def add_content_analysis_to_csv():
    """
    Main function to read CSV, analyze content, and create enhanced CSV.
    """
    # Check if debug mode is enabled
    DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')
    
    # Get configuration from environment variables
    input_file = os.getenv("CONTENT_FILE", "toc_with_metadata.csv")  # Use metadata file as input
    output_file = os.getenv("CONTENT_OUTPUT_FILE", "toc_with_content.csv")
    base_path = os.getenv("BASE_PATH")  # Base path where the markdown files are located

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
        print("Make sure to run add-metadata.py first to create the metadata file.")
        return
    
    print(f"Reading CSV file: {input_path}")
    if DEBUG:
        print(f"Base path for files: {base_path}")
    
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    # Change column name from Href to filename
    if 'Href' in df.columns:
        df = df.rename(columns={'Href': 'filename'})
    
    # Add new columns for content analysis
    df['has_tabs'] = False
    df['tab_count'] = 0
    df['tab_formats'] = ""
    df['has_images'] = False
    df['image_count'] = 0
    df['portal_steps'] = False
    df['has_code_blocks'] = False
    df['code_block_count'] = 0
    df['code_languages'] = ""
    df['has_code_refs'] = False
    df['code_ref_count'] = 0
    df['contains_link_no_param'] = False
    df['Contains_link_with_param'] = False
    
    # Process each row
    total_rows = len(df)
    processed_files = 0
    analyzed_files = 0
    
    for index, row in df.iterrows():
        filename = row.get('filename', '')
        
        if DEBUG:
            if index % 50 == 0:  # Progress indicator
                print(f"Processing row {index + 1}/{total_rows}")
        
        # Only analyze files that were found in the previous step
        if row.get('file_found', False):
            # Resolve the file path
            file_path = resolve_file_path(filename, base_path)
            
            if file_path:
                # Analyze content
                analysis = analyze_content(file_path)
                
                # Set the analysis results
                df.at[index, 'has_tabs'] = analysis['has_tabs']
                df.at[index, 'tab_count'] = analysis['tab_count']
                df.at[index, 'tab_formats'] = ', '.join(analysis['tab_formats']) if analysis['tab_formats'] else ""
                df.at[index, 'has_images'] = analysis['has_images']
                df.at[index, 'image_count'] = analysis['image_count']
                df.at[index, 'portal_steps'] = analysis['portal_steps']
                df.at[index, 'has_code_blocks'] = analysis['has_code_blocks']
                df.at[index, 'code_block_count'] = analysis['code_block_count']
                df.at[index, 'code_languages'] = ', '.join(analysis['code_languages']) if analysis['code_languages'] else ""
                df.at[index, 'has_code_refs'] = analysis['has_code_refs']
                df.at[index, 'code_ref_count'] = analysis['code_ref_count']
                # Set new link analysis columns
                df.at[index, 'contains_link_no_param'] = analysis.get('contains_link_no_param', False)
                df.at[index, 'Contains_link_with_param'] = analysis.get('Contains_link_with_param', False)
                
                analyzed_files += 1
                
        processed_files += 1
    
    # Save the enhanced CSV
    df.to_csv(output_path, index=False)
    
    print(f"\nProcessing complete!")
    print(f"Total rows: {total_rows}")
    print(f"Files processed: {processed_files}")
    print(f"Files analyzed: {analyzed_files}")
    print(f"Enhanced CSV saved to: {output_path}")
    
    # Show content analysis statistics
    files_with_tabs = len(df[df['has_tabs'] == True])
    files_with_images = len(df[df['has_images'] == True])
    files_with_portal_steps = len(df[df['portal_steps'] == True])
    files_with_code_blocks = len(df[df['has_code_blocks'] == True])
    files_with_code_refs = len(df[df['has_code_refs'] == True])
    total_tabs = df['tab_count'].sum()
    total_images = df['image_count'].sum()
    total_code_blocks = df['code_block_count'].sum()
    total_code_refs = df['code_ref_count'].sum()
    
    print(f"\nContent Analysis Statistics:")
    print(f"Files with tabs: {files_with_tabs}")
    print(f"Total tab instances: {total_tabs}")
    print(f"Files with images: {files_with_images}")
    print(f"Total image instances: {total_images}")
    print(f"Files with portal steps: {files_with_portal_steps}")
    print(f"Files with code blocks: {files_with_code_blocks}")
    print(f"Total code block instances: {total_code_blocks}")
    print(f"Files with code refs: {files_with_code_refs}")
    print(f"Total code ref instances: {total_code_refs}")
    
    # Show most common tab formats (debug mode only)
    if DEBUG and files_with_tabs > 0:
        all_tab_formats = []
        for _, row in df.iterrows():
            if row['tab_formats']:
                all_tab_formats.extend([fmt.strip() for fmt in row['tab_formats'].split(',')])
        
        if all_tab_formats:
            from collections import Counter
            tab_format_counts = Counter(all_tab_formats)
            print(f"\nMost common tab formats:")
            for fmt, count in tab_format_counts.most_common(10):
                print(f"  {fmt}: {count} files")
    
    # Show most common code languages (debug mode only)
    if DEBUG and files_with_code_blocks > 0:
        all_code_languages = []
        for _, row in df.iterrows():
            if row['code_languages']:
                all_code_languages.extend([lang.strip() for lang in row['code_languages'].split(',')])
        
        if all_code_languages:
            from collections import Counter
            code_language_counts = Counter(all_code_languages)
            print(f"\nMost common code languages:")
            for lang, count in code_language_counts.most_common(15):
                print(f"  {lang}: {count} files")

if __name__ == "__main__":
    add_content_analysis_to_csv()
