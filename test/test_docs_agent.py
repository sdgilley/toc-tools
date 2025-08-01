#!/usr/bin/env python3
"""
Example script showing how to use the docs_agent function to query documentation URLs.
"""

import sys
import os
sys.path.insert(0, '../utils')

from docs_agent import query_docs_agent

def main():
    """
    Example usage of the docs_agent function.
    """
    # Example URLs to test
    test_urls = [
        "https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/deployments-overview",
        "https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/sdk-overview"
    ]
    
    print("Testing docs agent with multiple URLs...\n")
    
    for i, url in enumerate(test_urls, 1):
        print(f"Test {i}: {url}")
        print("-" * 60)
        
        response = query_docs_agent(url)
        
        if response:
            print(f"Response: {response[:200]}...")  # Show first 200 characters
        else:
            print("No response received")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
