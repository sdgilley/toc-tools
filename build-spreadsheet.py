"""
This script reads a YAML Table of Contents (TOC) file from a specified learn docs repository,
flattens the TOC structure, generates URLs based on the href values, and exports the results to a CSV file.
It handles different href formats, including relative paths and absolute URLs, and includes a column    
indicating whether the href is part of the main TOC or another TOC.
"""

import pandas as pd
import yaml
import os
import utils.flatten_toc as f 
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

toc_file = os.getenv("TOC_FILE")  # path to the TOC YAML file
url_path = os.getenv("URL_PATH")  # base URL for the articles
output_file = os.getenv("OUTPUT_FILE")  # output file name

# Get the directory of the current script, write the output file in the same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, output_file)

# Read the TOC YAML file
with open(toc_file, 'r', encoding='utf-8') as file:
    toc = yaml.safe_load(file)

# Flatten the TOC structure
toc_items = toc.get("items", [])
flattened_toc = f.flatten_toc(toc_items, url_path)

# Convert the flattened TOC to a DataFrame
toc_df = pd.DataFrame(flattened_toc)
# remove rows without an href value or blank href value
toc_df = toc_df[toc_df['Href'].str.strip() != ""]
toc_df = toc_df[toc_df['Href'].notna()]
# Write to the output CSV file
toc_df.to_csv(file_path, index=False)

print(f"TOC with URLs exported to {file_path}")