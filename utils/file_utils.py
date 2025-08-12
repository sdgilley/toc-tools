#!/usr/bin/env python3
"""
Common utility functions for file processing and metadata extraction.
"""

import pandas as pd
import os
import re
import yaml

def resolve_file_path(href, base_path):
    """
    Resolve the full file path based on href and base path.
    
    Args:
        href (str): The href value from the CSV
        base_path (str): Base path to resolve relative paths
        
    Returns:
        str: Full path to the file, or None if file doesn't exist
    """
    # Handle NaN/None values
    if pd.isna(href) or not href or str(href).strip() == "":
        return None
    
    href = str(href).strip()
    
    # Remove query parameters from href (everything after ?)
    href = href.split('?')[0]
    
    # Handle different types of hrefs
    if href.startswith("http"):
        # External URLs - can't read metadata
        return None
    elif href.startswith("/"):
        # Absolute path - might need to be resolved relative to docs root
        # Remove leading slash and combine with base path
        relative_path = href.lstrip("/")
        full_path = os.path.join(base_path, relative_path)
    elif href.startswith(".."):
        # Handle relative paths that go up directories
        # Use os.path.normpath to properly resolve .. paths
        full_path = os.path.normpath(os.path.join(base_path, href))
    else:
        # Regular relative path
        # First try resolving relative to the base_path
        full_path = os.path.join(base_path, href)
        
        # If file doesn't exist and this looks like it might be a sibling directory,
        # try resolving relative to the parent of base_path
        if not os.path.exists(full_path) and '/' in href:
            # Check if this might be a sibling directory by trying parent path
            parent_base_path = os.path.dirname(base_path)
            alternative_path = os.path.join(parent_base_path, href)
            if os.path.exists(alternative_path):
                full_path = alternative_path
    
    # Ensure it's a markdown file if it doesn't already have an extension
    if not full_path.endswith('.md') and '.' not in os.path.basename(full_path):
        full_path += '.md'
    
    # Check if file exists
    if os.path.exists(full_path):
        return full_path
    
    return None

def extract_front_matter(file_path):
    """
    Extract YAML front matter from a markdown file.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        dict: Dictionary containing the front matter metadata, or empty dict if none found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove BOM character if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        # Check if file starts with YAML front matter (---)
        if not content.startswith('---'):
            return {}
        
        # Find the end of the front matter
        end_match = re.search(r'\n---\s*\n', content)
        if not end_match:
            return {}
        
        # Extract the YAML content between the --- markers
        yaml_content = content[3:end_match.start()]
        
        # Parse the YAML
        metadata = yaml.safe_load(yaml_content)
        return metadata if metadata else {}
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}

def read_file_content(file_path):
    """
    Read the full content of a markdown file.
    
    Args:
        file_path (str): Path to the markdown file
        
    Returns:
        str: File content, or empty string if error
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove BOM character if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        return content
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def load_pivot_mapping(pivot_map_file):
    """
    Load pivot group mapping from YAML file.
    
    Args:
        pivot_map_file (str): Path to the zone-pivot-groups.yml file
        
    Returns:
        dict: Dictionary mapping pivot group IDs to their details
    """
    if not pivot_map_file or not os.path.exists(pivot_map_file):
        print(f"Pivot map file not found: {pivot_map_file}")
        return {}
    
    try:
        with open(pivot_map_file, 'r', encoding='utf-8') as file:
            content = yaml.safe_load(file)
        
        # Create a mapping from group ID to group details
        pivot_mapping = {}
        if content and 'groups' in content:
            for group in content['groups']:
                if 'id' in group:
                    pivot_mapping[group['id']] = group
        
        return pivot_mapping
        
    except Exception as e:
        print(f"Error loading pivot mapping file {pivot_map_file}: {e}")
        return {}

def resolve_pivot_groups(pivot_ids, pivot_mapping):
    """
    Resolve pivot group IDs to their individual pivot IDs.
    
    Args:
        pivot_ids (str): Comma-separated pivot group IDs
        pivot_mapping (dict): Mapping from pivot group IDs to their details
        
    Returns:
        list: List of individual pivot IDs from the pivot groups
    """
    if not pivot_ids or not pivot_mapping:
        return []
    
    # Split by comma and clean up whitespace
    group_ids = [id.strip() for id in str(pivot_ids).split(',')]
    
    # Collect all pivot IDs from the specified groups
    all_pivot_ids = []
    for group_id in group_ids:
        if group_id in pivot_mapping:
            group = pivot_mapping[group_id]
            # Get the pivots list from this group
            if 'pivots' in group:
                for pivot in group['pivots']:
                    if 'id' in pivot:
                        all_pivot_ids.append(pivot['id'])
            else:
                # If no pivots found, use the group ID as fallback
                all_pivot_ids.append(group_id)
        else:
            # If group not found in mapping, use the ID as-is
            all_pivot_ids.append(group_id)
    
    return all_pivot_ids
