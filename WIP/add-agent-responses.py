#!/usr/bin/env python3
"""
This script processes a CSV file, runs the docs agent for each URL,
and adds the agent response as 4 new columns: HUB-ONLY, CODE, TABS, PORTAL.

Expected agent response format:
{
  "HUB-ONLY": true,
  "CODE": true,
  "TABS": false,
  "PORTAL": false,
  "SCREENSHOTS": true
}

All values are expected to be boolean (true/false) and will be converted to strings.
"""

import pandas as pd
import os
import json
import re
import sys
import time
import dotenv
from pathlib import Path

# Add utils to path for importing docs_agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
from docs_agent import query_docs_agent

# Load environment variables
dotenv.load_dotenv()

def extract_json_from_response(response):
    """
    Extract JSON data from the agent response.
    
    Args:
        response (str): The agent's response text
        
    Returns:
        dict: Parsed JSON data, or dict with default values if parsing fails
    """
    if not response:
        return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": ""}
    
    try:
        # Look for JSON content in the response
        # Handle cases where response might be wrapped in markdown code blocks
        json_match = re.search(r'```json\s*\n?(.*?)\n?```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON-like content between curly braces
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # If no JSON found, return the raw response in a note
                return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": "", "RESPONSE_NOTE": response[:100]}
        
        # Parse the JSON
        data = json.loads(json_str)
        
        # Extract the expected fields with defaults
        result = {
            "HUB-ONLY": str(data.get("HUB-ONLY", "")),
            "CODE": str(data.get("CODE", "")),
            "TABS": str(data.get("TABS", "")),
            "PORTAL": str(data.get("PORTAL", "")),
            "SCREENSHOTS": str(data.get("SCREENSHOTS", ""))
        }
        
        return result
        
    except (json.JSONDecodeError, Exception) as e:
        # Note: debug is not available in this function context, so we'll skip debug logging here
        # Return the raw response in a note field
        return {"HUB-ONLY": "", "CODE": "", "TABS": "", "PORTAL": "", "SCREENSHOTS": "", "PARSE_ERROR": str(e)[:100]}

def process_csv_with_agent():
    """
    Main function to process CSV file and add agent responses.
    """
    # Get configuration from environment variables
    input_file = os.getenv("OUTPUT_FILE", "toc.csv")
    output_file = os.getenv("AGENT_OUTPUT_FILE", "toc_with_agent_responses.csv")
    delay_seconds = float(os.getenv("AGENT_DELAY_SECONDS", "2"))  # Delay between requests
    resume_processing = os.getenv("RESUME_PROCESSING", "false").lower() == "true"
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay = float(os.getenv("RETRY_DELAY_SECONDS", "30"))  # Delay after quota errors
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return
    
    print(f"Reading CSV file: {input_path}")
    print(f"Output file: {output_path}")
    if debug:
        print(f"Delay between requests: {delay_seconds} seconds")
        print(f"Resume processing: {resume_processing}")
        print(f"Max retries: {max_retries}")
        print(f"Retry delay after quota errors: {retry_delay} seconds")
        print(f"Debug mode: {debug}")
    
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    # Check if this is a resume operation
    if resume_processing and os.path.exists(output_path):
        if debug:
            print(f"Resuming from existing output file: {output_path}")
        existing_df = pd.read_csv(output_path)
        
        # Ensure we have the same structure
        required_columns = ['HUB-ONLY', 'CODE', 'TABS', 'PORTAL', 'SCREENSHOTS', 'AGENT_PROCESSED', 'AGENT_ERROR']
        for col in required_columns:
            if col not in existing_df.columns:
                existing_df[col] = ""
                if col == 'AGENT_PROCESSED':
                    existing_df[col] = False
        
        df = existing_df
        already_processed = len(df[df['AGENT_PROCESSED'] == True])
        if debug:
            print(f"Found {already_processed} already processed rows")
    else:
        # Add new columns for agent responses
        df['HUB-ONLY'] = ""
        df['CODE'] = ""
        df['TABS'] = ""
        df['PORTAL'] = ""
        df['SCREENSHOTS'] = ""
        df['AGENT_PROCESSED'] = False
        df['AGENT_ERROR'] = ""
    
    # Process each row
    total_rows = len(df)
    processed_count = 0
    success_count = len(df[df['AGENT_PROCESSED'] == True])  # Count existing successes
    error_count = 0
    skipped_count = 0
    quota_errors = 0
    
    print(f"\nProcessing {total_rows} rows...")
    
    for index, row in df.iterrows():
        # Skip if already processed
        if row.get('AGENT_PROCESSED', False):
            skipped_count += 1
            continue
            
        url = row.get('URL', '')
        
        # Progress indicator
        processed_count += 1
        remaining = total_rows - success_count - error_count - skipped_count
        if debug:
            print(f"\nProcessing {processed_count}/{remaining} remaining: {url}")
        
        # Skip if no URL or if it's not a learn.microsoft.com URL
        if not url or not url.startswith('https://learn.microsoft.com'):
            if debug:
                print(f"  Skipping: Not a valid learn.microsoft.com URL")
            df.at[index, 'AGENT_ERROR'] = "Invalid or missing URL"
            error_count += 1
            continue
        
        # Retry logic for quota limits
        for attempt in range(max_retries + 1):
            try:
                # Query the docs agent
                if debug:
                    print(f"  Querying agent... (attempt {attempt + 1}/{max_retries + 1})")
                response = query_docs_agent(url)
                
                if response:
                    # Extract JSON data from response
                    json_data = extract_json_from_response(response)
                    
                    # Update the dataframe
                    df.at[index, 'HUB-ONLY'] = json_data.get('HUB-ONLY', '')
                    df.at[index, 'CODE'] = json_data.get('CODE', '')
                    df.at[index, 'TABS'] = json_data.get('TABS', '')
                    df.at[index, 'PORTAL'] = json_data.get('PORTAL', '')
                    df.at[index, 'SCREENSHOTS'] = json_data.get('SCREENSHOTS', '')
                    df.at[index, 'AGENT_PROCESSED'] = True
                    
                    # Handle any parsing errors or notes
                    if 'RESPONSE_NOTE' in json_data:
                        df.at[index, 'AGENT_ERROR'] = f"Raw response: {json_data['RESPONSE_NOTE']}"
                    elif 'PARSE_ERROR' in json_data:
                        df.at[index, 'AGENT_ERROR'] = f"Parse error: {json_data['PARSE_ERROR']}"
                    else:
                        df.at[index, 'AGENT_ERROR'] = ""  # Clear any previous errors
                    
                    success_count += 1
                    if debug:
                        print(f"  ✅ Success: HUB-ONLY={json_data.get('HUB-ONLY')}, CODE={json_data.get('CODE')}, TABS={json_data.get('TABS')}, PORTAL={json_data.get('PORTAL')}, SCREENSHOTS={json_data.get('SCREENSHOTS')}")
                    break  # Success, exit retry loop
                    
                else:
                    if attempt == max_retries:
                        df.at[index, 'AGENT_ERROR'] = "No response from agent after retries"
                        error_count += 1
                        if debug:
                            print(f"  ❌ No response from agent after {max_retries + 1} attempts")
                    else:
                        if debug:
                            print(f"  ⚠️ No response, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if this is a quota/rate limit error
                if any(keyword in error_msg for keyword in ['quota', 'rate', 'limit', 'throttle', '429', 'too many requests']):
                    quota_errors += 1
                    if attempt == max_retries:
                        df.at[index, 'AGENT_ERROR'] = f"Quota error after retries: {str(e)[:150]}"
                        error_count += 1
                        if debug:
                            print(f"  ❌ Quota error after {max_retries + 1} attempts: {e}")
                    else:
                        if debug:
                            print(f"  ⚠️ Quota error (#{quota_errors}), waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                else:
                    # Non-quota error, don't retry
                    df.at[index, 'AGENT_ERROR'] = str(e)[:200]  # Limit error message length
                    error_count += 1
                    if debug:
                        print(f"  ❌ Error: {e}")
                    break  # Exit retry loop for non-quota errors
        
        # Add delay between requests to avoid rate limiting
        if processed_count < remaining:  # Don't delay after the last request
            if debug:
                print(f"  Waiting {delay_seconds} seconds...")
            time.sleep(delay_seconds)
        
        # Save progress every 5 rows for large spreadsheets
        if processed_count % 5 == 0:
            if debug:
                print(f"  💾 Saving progress... ({success_count} successful, {error_count} errors, {skipped_count} skipped)")
            df.to_csv(output_path, index=False)
    
    # Save the final result
    df.to_csv(output_path, index=False)
    
    print(f"\n" + "="*80)
    print(f"Processing complete!")
    print(f"Total rows in spreadsheet: {total_rows}")
    print(f"Successfully processed: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Skipped (already processed): {skipped_count}")
    print(f"Quota errors encountered: {quota_errors}")
    print(f"Enhanced CSV saved to: {output_path}")
    
    # Show completion percentage
    completion_rate = (success_count / total_rows) * 100 if total_rows > 0 else 0
    print(f"Completion rate: {completion_rate:.1f}%")
    
    # Show some statistics
    hub_only_true = len(df[df['HUB-ONLY'].str.lower() == 'true'])
    hub_only_false = len(df[df['HUB-ONLY'].str.lower() == 'false'])
    code_true = len(df[df['CODE'].str.lower() == 'true'])
    tabs_true = len(df[df['TABS'].str.lower() == 'true'])
    portal_true = len(df[df['PORTAL'].str.lower() == 'true'])
    screenshots_true = len(df[df['SCREENSHOTS'].str.lower() == 'true'])
    
    print(f"\nAgent Response Statistics:")
    print(f"HUB-ONLY = True: {hub_only_true}")
    print(f"HUB-ONLY = False: {hub_only_false}")
    print(f"CODE = True: {code_true}")
    print(f"TABS = True: {tabs_true}")
    print(f"PORTAL = True: {portal_true}")
    print(f"SCREENSHOTS = True: {screenshots_true}")
    
    # Show resume instructions if needed
    if error_count > 0 or success_count < total_rows:
        print(f"\n💡 To resume processing remaining rows, set RESUME_PROCESSING=true in your .env file and run again.")

if __name__ == "__main__":
    process_csv_with_agent()
