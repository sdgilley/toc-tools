#!/usr/bin/env python3
"""
Example of using the generic merge_excel_data function for custom merges.
This demonstrates how to merge data from an Excel file with flexible positioning.
"""

import pandas as pd
from utils.excel_utils import merge_excel_data

def main():
    """Example usage of the generic merge function."""
    
    # Create sample DataFrame (you would typically load this from CSV)
    sample_data = {
        'URL': [
            'https://docs.microsoft.com/article1',
            'https://docs.microsoft.com/article2', 
            'https://docs.microsoft.com/article3',
            'https://docs.microsoft.com/article4'
        ],
        'filename': ['article1.md', 'article2.md', 'article3.md', 'article4.md'],
        'title': ['Article 1', 'Article 2', 'Article 3', 'Article 4'],
        'author': ['author1', 'author2', 'author3', 'author4']
    }
    df = pd.DataFrame(sample_data)
    
    print("Original DataFrame:")
    print(df.to_string(index=False))
    print()
    
    # Example 1: Merge Excel data (new columns always appear first)
    print("=== Example 1: Basic merge with new columns FIRST ===")
    df_merged = merge_excel_data(
        df=df.copy(),
        excel_file_path="C:/Users/sgilley/OneDrive - Microsoft/AI Foundry/foundry-toc.xlsx",
        key_column='URL',
        merge_columns=['URL', 'Notes', 'NextGen?', 'NextGen TOC'],
        sheet_name='Current Docs',
        debug=True
    )
    
    if len(df_merged.columns) > len(df.columns):
        print("Merged DataFrame (new columns first):")
        print("Columns:", list(df_merged.columns))
        print(df_merged.head().to_string(index=False))
    else:
        print("No merge occurred (file not found or no matching data)")
    print()
    
    # Example 2: Merge using filename as key column  
    print("=== Example 2: Merge using filename as key ===")
    
    # For this example, we'd need an Excel file that has filename column instead of URL
    # This would work if your Excel file has filename, Notes, etc.
    df_filename = merge_excel_data(
        df=df.copy(),
        excel_file_path="some-other-file.xlsx",  # This file would need filename column
        key_column='filename',
        merge_columns=['filename', 'status', 'priority', 'assigned_to'],
        debug=True
    )
    
    print("This example would work with an Excel file containing filename as key column")
    print()
    
    # Example 3: Using string format for merge_columns
    print("=== Example 3: Using string format for columns ===")
    df_string = merge_excel_data(
        df=df.copy(),
        excel_file_path="C:/Users/sgilley/OneDrive - Microsoft/AI Foundry/foundry-toc.xlsx",
        key_column='URL',
        merge_columns="URL,Notes,NextGen?",  # String format instead of list
        sheet_name='Current Docs',
        debug=True
    )
    
    if len(df_string.columns) > len(df.columns):
        print("Merged DataFrame (string columns format):")
        print("Columns:", list(df_string.columns))
    else:
        print("No merge occurred")
    

if __name__ == "__main__":
    main()