#!/usr/bin/env python3
"""
Statistics utilities for the metadata extraction system.
"""

import pandas as pd
import logging
from typing import Dict, Any


# Get logger for this module
logger = logging.getLogger(__name__)


def generate_statistics(df: pd.DataFrame, config: Dict[str, Any], processed_files: int, found_files: int) -> None:
    """
    Generate and log statistics about the processed data.
    
    Args:
        df: The processed dataframe
        config: Configuration dictionary containing metadata fields and flags
        processed_files: Number of files processed
        found_files: Number of files found
    """
    DEBUG = config.get('DEBUG', config.get('debug', False))
    metadata_fields = config['metadata_fields']
    has_pivot_field = config['has_pivot_field']
    metadata_flags = config['metadata_flags']
    
    total_rows = len(df)
    
    logger.info(f"Processing complete!")
    logger.info(f"Total rows: {total_rows}")
    logger.info(f"Files found: {found_files}")
    logger.info(f"Files processed: {processed_files}")
    logger.info(f"Main CSV saved to: {config['output_path']}")
    
    # Show statistics for configured metadata fields
    logger.info(f"Metadata Statistics:")
    
    # Statistics for regular metadata fields
    for field in metadata_fields:
        if field in df.columns:
            count = len(df[df[field].notna() & (df[field] != '')])
            logger.info(f"Files with {field}: {count}")
    
    # Statistics for pivot fields (only if zone_pivot_groups is in metadata fields)
    if has_pivot_field and 'pivot_id' in df.columns:
        pivots = df[df['pivot_id'] != '']['pivot_id'].value_counts()
        logger.info(f"Files with pivot_id: {len(df[df['pivot_id'] != ''])}")
        logger.info(f"Files with has_pivots: {len(df[df['has_pivots'] == True])}")
        logger.info(f"Files with pivot groups: {len(df[df['pivot_groups'] != ''])}")
    else:
        pivots = pd.Series(dtype=object)  # Empty series for debug section
    
    # Statistics for metadata flags
    for flag_name in metadata_flags.values():
        if flag_name in df.columns:
            count = len(df[df[flag_name] == True])
            logger.info(f"Files with {flag_name}: {count}")
    
    if DEBUG:
        # Show detailed breakdowns for first few metadata fields
        for field in metadata_fields[:3]:  # Limit to first 3 to avoid too much output
            if field in df.columns:
                field_values = df[df[field].notna() & (df[field] != '')][field].value_counts()
                if len(field_values) > 0:
                    logger.debug(f"Top {field} values:")
                    for value, count in field_values.head().items():
                        logger.debug(f"  {value}: {count} files")
            
        if has_pivot_field and len(pivots) > 0:
            logger.debug(f"Pivot group IDs found:")
            for pivot, count in pivots.head(10).items():
                logger.debug(f"  {pivot}: {count} files")
        
        # Show resolved pivot group names from comma-separated column (only if pivot columns exist)
        if has_pivot_field and 'pivot_groups' in df.columns:
            pivot_group_names = df[df['pivot_groups'] != '']['pivot_groups'].value_counts()
            if len(pivot_group_names) > 0:
                logger.debug(f"Resolved pivot group names:")
                for group_name, count in pivot_group_names.head(10).items():
                    logger.debug(f"  {group_name}: {count} files")