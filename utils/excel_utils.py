#!/usr/bin/env python3
"""
Excel and data merging utilities for the metadata extraction system.
"""

import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Union

try:
    import openpyxl
except ImportError:
    openpyxl = None


# Get logger for this module
logger = logging.getLogger(__name__)


def merge_excel_data(
    df: pd.DataFrame,
    excel_file_path: str,
    key_column: str,
    merge_columns: Union[str, List[str]],
    sheet_name: Optional[str] = None,
    debug: bool = False
) -> pd.DataFrame:
    """
    Generic function to merge data from an Excel file into a DataFrame.
    New columns are always inserted at the beginning for better visibility.
    
    Args:
        df: The dataframe to merge data into
        excel_file_path: Path to the Excel file to read from
        key_column: Column name to use for matching/joining (e.g., 'URL', 'filename')
        merge_columns: Either a comma-separated string or list of column names to merge.
                      First column should be the key column.
        sheet_name: Sheet name to read from (uses first sheet if None)
        debug: Enable debug logging
        
    Returns:
        The dataframe with merged data (unchanged if merge fails)
    """
    if not excel_file_path or not os.path.exists(excel_file_path):
        if debug:
            logger.debug(f"Excel file not found or not specified: {excel_file_path}")
        return df
        
    if not openpyxl:
        logger.warning("openpyxl not available for reading Excel files")
        return df
    
    try:
        # Clean the file path
        excel_file_path = excel_file_path.strip('"\'')
        
        if debug:
            logger.debug(f"Merging from Excel file: {excel_file_path}")
            logger.debug(f"Key column: {key_column}")
        
        # Read Excel file
        if sheet_name:
            df_existing = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        else:
            df_existing = pd.read_excel(excel_file_path)
            
        # Parse merge columns
        if isinstance(merge_columns, str):
            desired_columns = [col.strip() for col in merge_columns.split(',')]
        else:
            desired_columns = list(merge_columns)
        
        # Validate columns exist in source file
        available_cols = df_existing.columns.tolist()
        existing_merge_columns = [col for col in desired_columns if col in available_cols]
        
        if key_column not in existing_merge_columns:
            if debug:
                logger.debug(f"Key column '{key_column}' not found in Excel file")
                logger.debug(f"Available columns: {available_cols}")
            return df
            
        if len(existing_merge_columns) < 2:  # Need key + at least one other column
            if debug:
                logger.debug(f"Insufficient merge columns found")
                logger.debug(f"Looking for: {desired_columns}")
                logger.debug(f"Found: {existing_merge_columns}")
            return df
        
        # Prepare source data
        df_existing = df_existing[existing_merge_columns].drop_duplicates(subset=[key_column], keep='first')
        
        if debug:
            logger.debug(f"Source data: {len(df_existing)} unique records")
            logger.debug(f"Merge columns: {existing_merge_columns}")
        
        # Check if key column exists in target dataframe
        if key_column not in df.columns:
            logger.warning(f"Key column '{key_column}' not found in target dataframe")
            return df
        
        # Store original column order for positioning
        original_columns = df.columns.tolist()
        
        # Drop any existing merge columns (except key column) to avoid conflicts
        merge_data_columns = [col for col in existing_merge_columns if col != key_column]
        columns_to_drop = [col for col in merge_data_columns if col in df.columns]
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
            if debug:
                logger.debug(f"Dropped existing columns: {columns_to_drop}")
        
        # Perform the merge
        df_merged = df.merge(df_existing, on=key_column, how='left')
        
        # Always put new columns at the very beginning for maximum visibility
        current_cols = df_merged.columns.tolist()
        new_cols = [col for col in merge_data_columns if col in current_cols]
        other_cols = [col for col in current_cols if col not in new_cols]
        
        # Reorder: new columns first, then all original columns
        reordered_cols = new_cols + other_cols
        df_merged = df_merged[reordered_cols]
        
        # Log merge results
        merged_count = sum(df_merged[col].notna().sum() for col in merge_data_columns if col in df_merged.columns)
        logger.info(f"Successfully merged {len(merge_data_columns)} columns from Excel: {merged_count} total data points")
        
        return df_merged
        
    except Exception as e:
        logger.error(f"Error merging Excel data: {e}")
        return df


def merge_external_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Legacy wrapper function for backwards compatibility with existing pipeline.
    Merges existing Excel file data using environment variables for configuration.
    
    Args:
        df: The dataframe to merge data into
        config: Configuration dictionary containing merge settings
    
    Returns:
        The dataframe with merged data (may be unchanged if merge disabled)
    """
    DEBUG = config.get('DEBUG', config.get('debug', False))
    
    # Check if merge is enabled
    merge_existing = os.getenv("MERGE_EXISTING", "False").lower() in ('true', '1', 'yes')
    existing_excel_file = os.getenv("EXISTING_EXCEL_FILE")
    
    if DEBUG:
        logger.debug(f"MERGE_EXISTING = {merge_existing}")
        logger.debug(f"EXISTING_EXCEL_FILE = '{existing_excel_file}'")
    
    if not merge_existing:
        if DEBUG and existing_excel_file:
            logger.debug("Skipping existing Excel file merge (MERGE_EXISTING=False)")
        return df
    
    if not existing_excel_file:
        if DEBUG:
            logger.debug("No EXISTING_EXCEL_FILE specified")
        return df
    
    # Get configuration from environment variables
    tab_name = os.getenv('EXISTING_FILE_TAB_NAME', 'Current Docs')
    merge_columns_config = os.getenv("MERGE_COLUMNS", "URL,Notes,NextGen?,NextGen TOC")
    
    if DEBUG:
        logger.debug(f"Using sheet: {tab_name}")
        logger.debug(f"Merge columns: {merge_columns_config}")
    
    # Use the generic merge function
    return merge_excel_data(
        df=df,
        excel_file_path=existing_excel_file,
        key_column='URL',  # Default key column for pipeline
        merge_columns=merge_columns_config,
        sheet_name=tab_name,
        debug=DEBUG
    )