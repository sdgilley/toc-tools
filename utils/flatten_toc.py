# Function to flatten a TOC structure with full parent hierarchy

import yaml
import os

def flatten_toc(items, url_path, parent_path=None, base_toc_dir=None):
    rows = []
    for item in items:
        name = item.get("name", "")
        href = item.get("href", "")
        parent = parent_path if parent_path else ""
        current_path = f"{parent} > {name}" if parent else name
        otherToc = ""

        # Check if href points to another TOC file
        if href and href.endswith('.yml'):
            # This is a reference to another TOC file
            nested_toc_path = None
            nested_relative_dir = ""
            
            if base_toc_dir:
                if href.startswith(".."):
                    # Relative path going up directories
                    nested_toc_path = os.path.join(base_toc_dir, href)
                    nested_relative_dir = os.path.dirname(href)
                elif href.startswith("/"):
                    # Absolute path - we can't process these
                    pass
                else:
                    # Relative path in same or subdirectory
                    nested_toc_path = os.path.join(base_toc_dir, href)
                    nested_relative_dir = os.path.dirname(href)
            
            if nested_toc_path and os.path.exists(nested_toc_path):
                try:
                    # Load the nested TOC file
                    with open(nested_toc_path, 'r', encoding='utf-8') as nested_file:
                        nested_toc = yaml.safe_load(nested_file)
                    
                    # Get the nested TOC items and adjust their href paths
                    nested_items = nested_toc.get("items", [])
                    
                    # Adjust href paths in nested items to include directory structure
                    def adjust_nested_hrefs(items, relative_dir):
                        for item in items:
                            if item.get("href") and not item["href"].startswith(("http", "/", "..")):
                                # Prepend the relative directory to the href
                                if relative_dir:
                                    item["href"] = os.path.join(relative_dir, item["href"]).replace("\\", "/")
                            # Recursively adjust nested items
                            if "items" in item:
                                adjust_nested_hrefs(item["items"], relative_dir)
                    
                    if nested_relative_dir:
                        adjust_nested_hrefs(nested_items, nested_relative_dir)
                    
                    # Recursively flatten the nested TOC with the current path as parent
                    nested_base_dir = os.path.dirname(nested_toc_path)
                    nested_rows = flatten_toc(nested_items, url_path, current_path, nested_base_dir)
                    rows.extend(nested_rows)
                    
                    # Skip adding the TOC file reference itself since we've added its contents
                    continue
                    
                except Exception as e:
                    print(f"Warning: Could not load nested TOC file {nested_toc_path}: {e}")
                    # Fall through to add the TOC reference as a regular item

        # Normalize href to show path relative to articles directory (add ai-foundry prefix for local files)
        normalized_href = href
        if href and href.startswith(".."):
            # For hrefs that go up directories, normalize to show the final path
            # relative to the articles base directory
            href_parts = href.split('/')
            
            # Count levels up and get remaining path
            up_levels = 0
            remaining_parts = []
            for part in href_parts:
                if part == '..':
                    up_levels += 1
                elif part:
                    remaining_parts.append(part)
            
            # Create normalized href showing path from articles directory
            if remaining_parts:
                normalized_href = '/'.join(remaining_parts)
                # Remove context parameter from href only
                if '?context=' in normalized_href:
                    normalized_href = normalized_href.split('?context=')[0]
        elif href and not href.startswith(("http", "/", "..")):
            # For local files that don't start with .., add ai-foundry prefix
            normalized_href = f"ai-foundry/{href}"
            # Remove context parameter if present
            if '?context=' in normalized_href:
                normalized_href = normalized_href.split('?context=')[0]
        
        # Generate URL based on the rules
        if not href:
            url = f"{url_path}/{name.replace(' ', '-').lower()}"
        elif href.startswith(".."):
            # Handle relative paths that go up directories
            # Remove the file extension first but keep context for URL
            clean_href = href.replace('.md', '').replace('.yml', '')
            
            # Resolve the relative path and make it relative to the base URL
            # Split the href into parts (before removing context)
            href_parts = clean_href.split('/')
            
            # Count how many levels up we need to go
            up_levels = 0
            remaining_parts = []
            for part in href_parts:
                if part == '..':
                    up_levels += 1
                elif part:  # Skip empty parts
                    remaining_parts.append(part)
            
            # Check if this points to ai-services (outside ai-foundry)
            if remaining_parts and remaining_parts[0] == 'ai-services':
                # For ai-services, use the Microsoft Learn base URL without ai-foundry
                relative_path = '/'.join(remaining_parts)
                url = f"https://learn.microsoft.com/azure/{relative_path}"
            else:
                # For other relative paths, stay within the base URL_PATH context
                if remaining_parts:
                    relative_path = '/'.join(remaining_parts)
                    url = f"{url_path.rstrip('/')}/{relative_path}"
                else:
                    url = url_path.rstrip('/')
            otherToc = "True"
        elif href.startswith("/"):
            url = f"https://learn.microsoft.com{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "True"
        else:
            url = f"{url_path}/{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "False"
        
        rows.append({"Parent Path": parent, "Name": name, "Href": normalized_href, "OtherTOC": otherToc, "URL": url})
        if "items" in item:
            rows.extend(flatten_toc(item["items"], url_path, current_path, base_toc_dir))
    return rows


# test the function with a sample TOC
if __name__ == "__main__":
    
    import yaml

    toc_file = "C:/GitPrivate/azure-ai-docs-pr/articles/ai-foundry/agents/toc.yml"  # your local repo
    
    # Read the TOC YAML file
    with open(toc_file, 'r', encoding='utf-8') as file:
        toc = yaml.safe_load(file)

    # Get the directory of the TOC file for resolving relative paths to nested TOCs
    toc_dir = os.path.dirname(os.path.abspath(toc_file))

    # Flatten the TOC structure
    toc_items = toc.get("items", [])
    flattened_toc = flatten_toc(toc_items, "https://learn.microsoft.com/azure/ai-foundry/agents", base_toc_dir=toc_dir)    # Print the flattened TOC
    print(f"Total items: {len(flattened_toc)}")
    
    # Show items with non-empty parent paths
    items_with_parents = [row for row in flattened_toc if row['Parent Path']]
    print(f"Items with parent paths: {len(items_with_parents)}")
    
    for i, row in enumerate(items_with_parents[:15]):  # Show first 15 items with parents
        print(f"Item {i+1}:")
        print(f"  Parent Path: '{row['Parent Path']}'")
        print(f"  Name: '{row['Name']}'")
        print(f"  Href: '{row['Href']}'")
        print()