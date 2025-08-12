# Function to flatten a TOC structure with full parent hierarchy

import yaml
import os

def flatten_toc(items, url_path, parent_path="", base_toc_dir="", toc_relative_dir=None):
    """
    Recursively flatten a TOC structure and generate URLs.
    
    Args:
        items: List of TOC items to flatten
        url_path: Base URL path for generating article URLs
        parent_path: Current parent path for nested items
        base_toc_dir: Base directory where the TOC file is located
        toc_relative_dir: Relative directory of the TOC from the base articles directory
    
    Returns:
        List of dictionaries representing flattened TOC rows
    """
    rows = []
    
    for item in items:
        name = item.get("name", "")
        href = item.get("href", "")
        
        # Debug specific items to see what we're processing
        # if href and ("concepts/" in href or "foundry-models" in href):
        #     print(f"Debug processing: name='{name}', href='{href}', toc_relative_dir='{toc_relative_dir}'")
        
        # Build the current path (parent path + current item name)
        current_path = parent_path + " > " + name if parent_path else name
        
        # Process href - normalize all hrefs to be relative to base path
        processed_href = href
        
        if href:
            if href.startswith("http"):
                # External URL - keep as is
                processed_href = href
                is_external = True
            elif href.endswith(".yml"):
                # Nested TOC file - recursively process it
                nested_toc_path = os.path.join(base_toc_dir, href)
                if os.path.exists(nested_toc_path):
                    try:
                        with open(nested_toc_path, 'r', encoding='utf-8') as nested_file:
                            nested_toc = yaml.safe_load(nested_file)
                            nested_items = nested_toc.get("items", [])
                            
                            # Get the directory of the nested TOC for further nested processing
                            nested_toc_dir = os.path.dirname(os.path.abspath(nested_toc_path))
                            
                            # Calculate the relative directory for the nested TOC
                            # This is needed because nested TOCs have their own relative path context
                            if toc_relative_dir:
                                # Get the relative path from the base path to the nested TOC directory
                                base_path_env = os.environ.get("BASE_PATH", "")
                                if base_path_env:
                                    nested_toc_relative_dir = os.path.relpath(nested_toc_dir, base_path_env)
                                    # Convert backslashes to forward slashes for consistency
                                    nested_toc_relative_dir = nested_toc_relative_dir.replace("\\", "/")
                                    # Handle case where nested TOC is in the base directory itself
                                    if nested_toc_relative_dir == ".":
                                        nested_toc_relative_dir = None
                                else:
                                    nested_toc_relative_dir = toc_relative_dir
                            else:
                                nested_toc_relative_dir = None
                            
                            # Recursively process nested TOC items
                            nested_rows = flatten_toc(nested_items, url_path, current_path, nested_toc_dir, nested_toc_relative_dir)
                            rows.extend(nested_rows)
                    except Exception as e:
                        print(f"Error processing nested TOC {href}: {e}")
                continue
            else:
                # Local file href - ensure it has proper directory prefix for base path resolution
                is_external = False
                
                # Handle relative paths (../../) by resolving them relative to the TOC directory
                if href.startswith("../"):
                    # For relative paths, we need to resolve them properly
                    # Since all hrefs should be relative to the base articles directory,
                    # and we know the toc_relative_dir, we can resolve the path
                    import posixpath
                    if toc_relative_dir:
                        # Join the toc relative directory with the href and normalize the path
                        combined_path = posixpath.join(toc_relative_dir, href)
                        processed_href = posixpath.normpath(combined_path)
                        # Ensure we don't have any remaining .. components
                        while processed_href.startswith("../"):
                            processed_href = processed_href[3:]
                        # print(f"Resolving relative path: {href} -> {processed_href} (via {toc_relative_dir})")
                    else:
                        # No toc_relative_dir, keep the relative path as-is but try to resolve it
                        processed_href = posixpath.normpath(href)
                        # Remove leading .. components if they go above root
                        while processed_href.startswith("../"):
                            processed_href = processed_href[3:]
                elif href.startswith("./"):
                    # Handle ./ paths by removing the ./ prefix
                    processed_href = href[2:]  # Remove "./"
                    if toc_relative_dir and not processed_href.startswith(toc_relative_dir + "/"):
                        processed_href = f"{toc_relative_dir}/{processed_href}"
                else:
                    # Not a relative path, check if we need to add the directory prefix
                    # Determine if this path should be at the root level (same level as current toc directory)
                    should_add_prefix = True
                    if toc_relative_dir:
                        # Check if the href already starts with the toc_relative_dir
                        if href.startswith(toc_relative_dir + "/"):
                            should_add_prefix = False
                        else:
                            # Check if this href represents a sibling directory to the current toc location
                            # For example: if toc_relative_dir is "ai-foundry" and href is "ai-services/something",
                            # then "ai-services" is a sibling to "ai-foundry" and shouldn't get the prefix
                            
                            # Count directory levels in toc_relative_dir 
                            # Note: toc_relative_dir shows depth from /articles/, but the TOC file itself
                            # may be deeper (e.g., in a subdirectory). We need to account for the actual
                            # file location depth, not just the directory name depth.
                            toc_depth = len([p for p in toc_relative_dir.split('/') if p])
                            
                            # Check the depth that this href represents
                            href_parts = [p for p in href.split('/') if p]
                            if len(href_parts) > 0:
                                # If href appears to be at the same level as the TOC's parent directory
                                # (i.e., both are immediate children of articles/), don't add prefix
                                # This is detected when href starts with what looks like a top-level directory name
                                # and the path depth suggests it's at the root articles level
                                
                                # Simple heuristic: if toc_relative_dir represents a top-level service directory
                                # and href looks like it's also a top-level service directory (like "ai-services/..."), 
                                # then they're siblings and href shouldn't get the prefix
                                if toc_depth >= 1:  # We're in a service directory or deeper
                                    # We're in a service directory, check if href is also a top-level service
                                    # by seeing if it doesn't already contain our toc directory
                                    first_href_part = href_parts[0]
                                    toc_first_part = toc_relative_dir.split('/')[0]
                                    # Only consider this a sibling if the href actually represents a different service
                                    # (i.e., it's not just a subdirectory within the current service)
                                    # Known sibling services that should use their own URLs:
                                    known_sibling_services = ["ai-services", "ai-search", "ai-studio"]
                                    if (first_href_part != toc_first_part and 
                                        first_href_part in known_sibling_services):
                                        # This is a known sibling service, don't add prefix
                                        should_add_prefix = False
                    
                    if should_add_prefix and toc_relative_dir:
                        processed_href = f"{toc_relative_dir}/{href}"
                    else:
                        processed_href = href
        else:
            is_external = False
        
        # Only add items with href (actual articles/links)
        if href and not href.endswith(".yml"):
            # Generate the full URL
            if is_external:
                full_url = href
            else:
                # New approach: construct URL based on the normalized path after /articles/
                # The processed_href already represents the path relative to /articles/
                
                # Check if this path represents a sibling directory to the current TOC location
                is_sibling_directory = False
                if toc_relative_dir:
                    path_parts = [p for p in processed_href.split('/') if p]
                    if len(path_parts) > 0:
                        first_part = path_parts[0]
                        toc_first_part = toc_relative_dir.split('/')[0]
                        # If the first part of the path is different from the TOC directory,
                        # and it contains subdirectories, this is likely a sibling directory
                        if first_part != toc_first_part and "/" in processed_href:
                            is_sibling_directory = True
                
                if is_sibling_directory:
                    # This is a sibling directory (like ai-services from ai-foundry TOC)
                    full_url = f"https://learn.microsoft.com/azure/{processed_href.lstrip('/')}"
                else:
                    # This is a regular file in the current service directory
                    if toc_relative_dir:
                        # Ensure the path includes the service directory if it doesn't already
                        if not processed_href.startswith(toc_relative_dir + "/") and not processed_href.startswith(toc_relative_dir.split('/')[-1] + "/"):
                            # For simple filenames, add the toc directory prefix
                            if "/" not in processed_href:
                                processed_href = f"{toc_relative_dir}/{processed_href}"
                    full_url = f"https://learn.microsoft.com/azure/{processed_href.lstrip('/')}"
            
            rows.append({
                "Parent Path": parent_path,
                "Name": name,
                "Href": processed_href,
                "URL": full_url,
                "Is External": is_external
            })
        
        # Process nested items
        if "items" in item:
            nested_rows = flatten_toc(item["items"], url_path, current_path, base_toc_dir, toc_relative_dir)
            rows.extend(nested_rows)
    
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
    flattened_toc = flatten_toc(toc_items, "https://learn.microsoft.com/azure/ai-foundry/agents", base_toc_dir=toc_dir, toc_relative_dir="ai-foundry/agents")    # Print the flattened TOC
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