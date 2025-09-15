import pandas as pd

def normalize_url(url, preserve_query=False):
    """
    Normalize a URL for consistency:
    - Remove '/en-us/'
    - Remove trailing '.md'
    - Remove trailing slashes
    - Ensure consistent domain format
    
    Args:
        url: The URL to normalize
        preserve_query: If True, preserve query parameters. If False, remove them.
                      Default is False for backward compatibility with URL matching.
    """
    if pd.isna(url):
        return ""
    url = str(url).strip()
    
    # Split URL into path and query if needed
    parts = url.split('?', 1)
    path = parts[0]
    query = parts[1] if len(parts) > 1 and preserve_query else None
    
    # Clean the path
    path = path.replace("/en-us/", "/")
    if path.endswith(".md"):
        path = path[:-3]
    path = path.rstrip("/")
    
    # Ensure consistent domain format
    if path.startswith("https://learn.microsoft.com/"):
        path = path.replace("https://learn.microsoft.com/azure/", "https://learn.microsoft.com/azure/")
    
    # Recombine with query if present and preserving
    if query:
        return f"{path}?{query}"
    return path

if __name__ == "__main__":
    # Debug usage example
    test_urls = [
        "https://learn.microsoft.com/en-us/azure/ai-foundry/what-is-azure-ai-foundry.md?context=/azure/ai-foundry/context/context",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code.md",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code",
        "https://learn.microsoft.com/azure/ai-foundry/quickstarts/get-started-code.md?foo=bar",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code?foo=bar"
    ]
    for url in test_urls:
        print(f"Original: {url}")
        print(f"Normalized: {normalize_url(url)}\n")
