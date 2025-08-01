#!/usr/bin/env python3
"""
Test script to verify nested TOC functionality
"""

import sys
import os
import yaml

# Add the parent directory to sys.path to import utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.flatten_toc as f

def test_nested_toc():
    """Test the nested TOC functionality"""
    
    toc_file = "/Users/sherigilley/git/toc-tools/test/main-toc.yml"
    url_path = "https://learn.microsoft.com/test"
    
    print("Testing nested TOC functionality...")
    print(f"Main TOC file: {toc_file}")
    print(f"URL path: {url_path}")
    print()
    
    # Read the main TOC file
    with open(toc_file, 'r', encoding='utf-8') as file:
        toc = yaml.safe_load(file)
    
    # Get the directory of the TOC file for resolving relative paths to nested TOCs
    toc_dir = os.path.dirname(os.path.abspath(toc_file))
    
    # Flatten the TOC structure with nested TOC support
    toc_items = toc.get("items", [])
    flattened_toc = f.flatten_toc(toc_items, url_path, base_toc_dir=toc_dir)
    
    print(f"Total flattened items: {len(flattened_toc)}")
    print()
    
    # Display results
    for i, item in enumerate(flattened_toc, 1):
        parent = item['Parent Path']
        name = item['Name']
        href = item['Href']
        other_toc = item['OtherTOC']
        url = item['URL']
        
        print(f"{i:2d}. Name: {name}")
        if parent:
            print(f"    Parent: {parent}")
        print(f"    Href: {href}")
        print(f"    Other TOC: {other_toc}")
        print(f"    URL: {url}")
        print()
    
    # Check that nested items are included
    nested_items = [item for item in flattened_toc if 'Advanced Topics' in item.get('Parent Path', '')]
    print(f"Items under 'Advanced Topics': {len(nested_items)}")
    
    extension_items = [item for item in flattened_toc if 'Extensions' in item.get('Parent Path', '')]
    print(f"Items under 'API Reference > Extensions': {len(extension_items)}")
    
    if nested_items and extension_items:
        print("\n✅ Test PASSED: Nested TOC files were successfully processed!")
    else:
        print("\n❌ Test FAILED: Nested TOC items were not found")
        
    return flattened_toc

if __name__ == "__main__":
    test_nested_toc()
