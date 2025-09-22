#!/usr/bin/env python3
"""
Excel and data merging utilities for the metadata extraction system.
"""

import os
import pandas as pd
import logging
from typing import Dict, Any

try:
    import openpyxl
except ImportError:
    openpyxl = None


# Get logger for this module
logger = logging.getLogger(__name__)


def merge_external_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Merge existing Excel file data if available and enabled.
    
    Args:
        df: The dataframe to merge data into
        config: Configuration dictionary containing merge settings
    
    Returns:
        The dataframe with merged data (may be unchanged if merge disabled)
    """
    DEBUG = config.get('DEBUG', config.get('debug', False))
    
    # Merge existing Excel file data if available and enabled
    merge_existing = os.getenv("MERGE_EXISTING", "False").lower() in ('true', '1', 'yes')
    existing_excel_file = os.getenv("EXISTING_EXCEL_FILE")
    
    if DEBUG:
        logger.debug(f"MERGE_EXISTING = {merge_existing}")
        logger.debug(f"EXISTING_EXCEL_FILE = '{existing_excel_file}'")
    
    if merge_existing and existing_excel_file:
        # Strip quotes and clean the path
        existing_excel_file = existing_excel_file.strip('"\'')
        if DEBUG:
            print(f"Debug: Cleaned EXISTING_EXCEL_FILE = '{existing_excel_file}'")
            print(f"Debug: File exists? {os.path.exists(existing_excel_file)}")
    
    if merge_existing and existing_excel_file and os.path.exists(existing_excel_file) and openpyxl:
        try:
            logger.info(f"Merging data from existing Excel file: {existing_excel_file}")
            
            # Read the data sheet from the existing Excel file
            tab_name = os.getenv('EXISTING_FILE_TAB_NAME')
            if DEBUG:
                print(f"[DEBUG] EXISTING_EXCEL_FILE: {existing_excel_file}")
                print(f"[DEBUG] EXISTING_FILE_TAB_NAME: {tab_name}")
            if tab_name and DEBUG:
                print(f"[DEBUG] Using tab name from env: {tab_name}")
            else:
                tab_name = 'Current Docs'  # Default sheet name
                if DEBUG:
                    print("[DEBUG] No tab name specified in env, using default sheet 'Current Docs'.")

            df_existing = pd.read_excel(existing_excel_file, sheet_name=tab_name)
            
            # Get merge columns from configuration
            merge_columns_config = os.getenv("MERGE_COLUMNS", "URL,Notes,NextGen?,NextGen TOC")
            available_cols = df_existing.columns.tolist()
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
                
                # Merge the data
                df = df.merge(df_existing, on=key_column, how='left')
                merged_count = df[merge_columns[1]].notna().sum() if len(merge_columns) > 1 else 0
                logger.info(f"Successfully merged existing data: {merged_count} URLs matched")
            else:
                if DEBUG:
                    print(f"Cannot merge - missing required columns")
                    print(f"Available columns in Excel: {available_cols}")
                    print(f"Looking for configured merge columns: {', '.join(desired_columns)}")
                    print(f"Key column '{key_column}' found: {key_column in available_cols}")
                    for col in desired_columns[1:]:  # Skip key column
                        print(f"'{col}' found: {col in available_cols}")
                
        except Exception as e:
            logger.error(f"Error reading existing Excel file: {e}")
    elif not merge_existing and existing_excel_file:
        if DEBUG:
            print("Skipping existing Excel file merge (MERGE_EXISTING=False)")
    elif existing_excel_file and not os.path.exists(existing_excel_file):
        logger.warning(f"Existing Excel file not found: {existing_excel_file}")
    elif existing_excel_file and not openpyxl:
        logger.warning("openpyxl not available for reading Excel files")
    
    return df