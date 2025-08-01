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

        # Generate URL based on the rules
        if not href:
            url = f"{url_path}/{name.replace(' ', '-').lower()}"
        elif href.startswith(".."):
            # Handle relative paths that go up directories
            # Remove the file extension first
            clean_href = href.replace('.md', '').replace('.yml', '')
            # Use os.path.normpath to resolve the .. paths, then convert to URL format
            url_path_parts = url_path.rstrip('/').split('/')
            href_parts = clean_href.split('/')
            
            # Start with the URL path parts
            result_parts = url_path_parts[:]
            
            # Process each part of the href
            for part in href_parts:
                if part == '..':
                    # Go up one level if possible
                    if len(result_parts) > 3:  # Keep https://learn.microsoft.com at minimum
                        result_parts.pop()
                elif part:  # Skip empty parts
                    result_parts.append(part)
            
            url = '/'.join(result_parts)
            otherToc = "True"
        elif href.startswith("/"):
            url = f"https://learn.microsoft.com{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "True"
        else:
            url = f"{url_path}/{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "False"
        
        rows.append({"Parent Path": parent, "Name": name, "Href": href, "OtherTOC": otherToc, "URL": url})
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