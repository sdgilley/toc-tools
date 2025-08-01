#!/usr/bin/env python3
"""
Test the JSON parsing functionality for agent responses.
"""

import json
import re

def extract_json_from_response(response):
    """
    Extract JSON data from the agent response.
    """
    if not response:
        return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": ""}
    
    try:
        # Look for JSON content in the response
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": "", "RESPONSE_NOTE": response[:100]}
        
        data = json.loads(json_str)
        result = {
            "HUB-ONLY": str(data.get("HUB-ONLY", "")),
            "CODE": str(data.get("CODE", "")),
            "TABS": str(data.get("TABS", "")),
            "PORTAL": str(data.get("PORTAL", "")),
            "SCREENSHOTS": str(data.get("SCREENSHOTS", ""))
        }
        return result
        
    except Exception as e:
        return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": "", "PARSE_ERROR": str(e)[:100]}

def test_parsing():
    """Test the JSON parsing with various response formats."""
    
    # Test case 1: Your example response
    test_response1 = '''Response: ```json
{
  "HUB-ONLY": "No",
  "CODE": true,
  "TABS": true,
  "PORTAL": false,
  "SCREENSHOTS": true
}```'''
    
    # Test case 2: Plain JSON without markdown
    test_response2 = '''{
  "HUB-ONLY": "Yes",
  "CODE": false,
  "TABS": false,
  "PORTAL": true,
  "SCREENSHOTS": false
}'''
    
    # Test case 3: Response with extra text
    test_response3 = '''Here is the analysis of the documentation:

```json
{
  "HUB-ONLY": "No",
  "CODE": true,
  "TABS": false,
  "PORTAL": false,
  "SCREENSHOTS": false
}
```

This document shows code examples but no tabs.'''
    
    test_cases = [
        ("Example response", test_response1),
        ("Plain JSON", test_response2),
        ("JSON with extra text", test_response3)
    ]
    
    print("Testing JSON parsing functionality...\n")
    
    for name, response in test_cases:
        print(f"Test: {name}")
        print(f"Input: {response[:60]}...")
        result = extract_json_from_response(response)
        print(f"Output: {result}")
        print("-" * 60)

if __name__ == "__main__":
    test_parsing()
