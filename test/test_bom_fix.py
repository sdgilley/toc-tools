#!/usr/bin/env python3

import os
import re
import yaml

def extract_front_matter(file_path):
    """
    Extract YAML front matter from a markdown file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove BOM character if present
        if content.startswith('\ufeff'):
            content = content[1:]
            print("BOM character found and removed")
        
        # Check if file starts with YAML front matter (---)
        if not content.startswith('---'):
            print("No front matter found")
            return {}
        
        # Find the end of the front matter
        end_match = re.search(r'\n---\s*\n', content)
        if not end_match:
            print("No end marker found")
            return {}
        
        # Extract the YAML content between the --- markers
        yaml_content = content[3:end_match.start()]
        print(f"YAML content:\n{yaml_content[:200]}...")
        
        # Parse the YAML
        metadata = yaml.safe_load(yaml_content)
        return metadata if metadata else {}
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return {}

# Test the specific file
file_path = "/Users/sherigilley/git/azure-ai-docs-pr/articles/ai-foundry/concepts/foundry-models-overview.md"
print(f"Testing file: {file_path}")
metadata = extract_front_matter(file_path)

print(f"\nExtracted metadata:")
for key, value in metadata.items():
    print(f"  {key}: {value}")

print(f"\nms.author: {metadata.get('ms.author', 'NOT FOUND')}")
print(f"description: {metadata.get('description', 'NOT FOUND')}")
