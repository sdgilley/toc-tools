#!/usr/bin/env python3
"""
Debug script to check the metadata extraction for a specific file
"""

import os
import dotenv
from utils.file_utils import extract_front_matter, resolve_file_path

# Load environment variables
dotenv.load_dotenv()

# Test the specific file that should have hub-only = true
href = "concepts/vulnerability-management.md"
base_path = os.getenv("BASE_PATH")

print(f"Testing file: {href}")
print(f"Base path: {base_path}")

# Resolve the file path
file_path = resolve_file_path(href, base_path)
print(f"Resolved path: {file_path}")

if file_path:
    # Extract metadata
    metadata = extract_front_matter(file_path)
    print(f"\nExtracted metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    # Check specifically for hub-only related fields
    print(f"\nChecking for hub-only indicators:")
    print(f"  'custom' field: {metadata.get('custom', 'NOT FOUND')}")
    print(f"  'hub-only' field: {metadata.get('hub-only', 'NOT FOUND')}")
    print(f"  'hub_only' field: {metadata.get('hub_only', 'NOT FOUND')}")
    
    # Test the hub-only detection logic (updated version)
    print(f"\nTesting hub-only detection logic:")
    
    hub_only_found = False
    
    # Check 'custom' field
    if 'custom' in metadata:
        custom_data = metadata['custom']
        if isinstance(custom_data, str):
            hub_only_found = 'hub-only' in custom_data.lower()
        elif isinstance(custom_data, list):
            hub_only_found = any('hub-only' in str(item).lower() for item in custom_data)
        elif isinstance(custom_data, dict):
            hub_only_found = any('hub-only' in str(value).lower() for value in custom_data.values())
        print(f"  Checked 'custom' field: {hub_only_found}")
    
    # Check 'ms.custom' field if not found in 'custom'
    if not hub_only_found and 'ms.custom' in metadata:
        custom_data = metadata['ms.custom']
        if isinstance(custom_data, str):
            hub_only_found = 'hub-only' in custom_data.lower()
        elif isinstance(custom_data, list):
            hub_only_found = any('hub-only' in str(item).lower() for item in custom_data)
        elif isinstance(custom_data, dict):
            hub_only_found = any('hub-only' in str(value).lower() for value in custom_data.values())
        print(f"  Checked 'ms.custom' field: {hub_only_found}")
    
    print(f"  Final hub-only result: {hub_only_found}")
    
    if not hub_only_found:
        print("  No 'hub-only' indicators found in any field")
else:
    print("File not found!")
