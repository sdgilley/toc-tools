# Function to flatten a TOC structure with full parent hierarchy

def flatten_toc(items, url_path, parent_path=None):
    rows = []
    for item in items:
        name = item.get("name", "")
        href = item.get("href", "")
        parent = parent_path if parent_path else ""
        current_path = f"{parent} > {name}" if parent else name
        otherToc = ""

        # Generate URL based on the rules
        if not href:
            url = f"{url_path}/{name.replace(' ', '-').lower()}"
        elif href.startswith(".."):
            url = f"https://learn.microsoft.com/{href[3:].replace('.md', '').replace('.yml', '')}"
            otherToc = "true"
        elif href.startswith("/"):
            url = f"https://learn.microsoft.com/{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "true"
        else:
            url = f"{url_path}/{href.replace('.md', '').replace('.yml', '')}"
            otherToc = "false"
        
        rows.append({"Parent Path": parent, "Name": name, "Href": href, "OtherTOC": otherToc, "URL": url})
        if "items" in item:
            rows.extend(flatten_toc(item["items"], url_path, current_path))
    return rows


# test the function with a sample TOC
if __name__ == "__main__":
    
    import yaml

    toc_file = "C:/GitPrivate/azure-ai-docs-pr/articles/ai-services/agents/toc.yml"  # your local repo
    
    # Read the TOC YAML file
    with open(toc_file, 'r', encoding='utf-8') as file:
        toc = yaml.safe_load(file)

    # Flatten the TOC structure
    toc_items = toc.get("items", [])
    flattened_toc = flatten_toc(toc_items, "https://learn.microsoft.com/azure/ai-services/agents")    # Print the flattened TOC
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