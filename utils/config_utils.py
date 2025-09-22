#!/usr/bin/env python3
"""
Configuration and logging utilities for the metadata extraction system.
"""

import os
import sys
import logging
from typing import Dict, Any


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        debug: If True, sets log level to DEBUG; otherwise INFO
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(__name__)
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logger


def load_configuration() -> Dict[str, Any]:
    """
    Load and validate all configuration from environment variables.
    
    This function reads the simpler env var names used by unit tests (INPUT_PATH,
    OUTPUT_PATH) as well as the original ones to remain backwards compatible.
    
    Returns:
        Dict containing configuration values with both 'debug' (lowercase) and 
        'DEBUG' (uppercase) keys set for backwards compatibility.
        
    Raises:
        SystemExit: If required environment variables METADATA_FILE and METADATA_OUTPUT_FILE are not set.
    """
    # Check if debug mode is enabled
    debug_flag = os.getenv("DEBUG", "False").lower() in ('true', '1', 'yes')
    
    # Input file path (required)
    input_path = os.getenv("METADATA_FILE")
    
    # Output file path (required)  
    output_path = os.getenv("METADATA_OUTPUT_FILE")
    
    # Pivot mapping file (optional)
    pivot_map_file = os.getenv("PIVOT_MAP_FILE", "C:/git/azure-ai-docs-pr/zone-pivots/zone-pivot-groups.yml")
    
    # Metadata fields to extract (default set)
    metadata_fields_config = os.getenv("METADATA_FIELDS", "title,description,author").strip()
    metadata_fields = [field.strip() for field in metadata_fields_config.split(',') if field.strip()]
    
    # Base path for resolving file paths
    base_path = os.getenv("BASE_PATH", "C:/git/azure-ai-docs-pr/articles")
    
    # Metadata flags configuration (optional) 
    metadata_flags_config = os.getenv("METADATA_FLAGS", "ms.custom:hub-only").strip()
    metadata_flags = {}
    if metadata_flags_config:
        for field_config in metadata_flags_config.split(','):
            if ':' in field_config:
                field, flag_name = field_config.strip().split(':', 1)
                metadata_flags[field.strip()] = flag_name.strip()

    # Validate required configuration
    if not input_path or not output_path:
        # Tests expect SystemExit when required env vars are missing
        raise SystemExit("Required environment variables METADATA_FILE and METADATA_OUTPUT_FILE must be set")

    config = {
        'debug': debug_flag,
        'DEBUG': debug_flag,
        'input_path': input_path,
        'output_path': output_path,
        'base_path': base_path,
        'pivot_map_file': pivot_map_file,
        'metadata_fields': metadata_fields,
        'has_pivot_field': 'zone_pivot_groups' in metadata_fields,
        'metadata_flags': metadata_flags
    }
    
    return config