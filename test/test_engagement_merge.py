
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from utils.url_normalizer import normalize_url

# Paths to test files
main_csv = "c:/git/toc-tools/foundry-toc.csv"
engagement_csv = "c:/git/toc-tools/engagement-aug.csv"

# Read main CSV
main_df = pd.read_csv(main_csv)
# Read engagement CSV
engage_df = pd.read_csv(engagement_csv)

# Only keep relevant columns from engagement
engage_cols = ["Url", "PageViews", "PVMoM", "Visitors", "Engagement"]
engage_df = engage_df[engage_cols]

# only keep relevant columns from main
main_cols = ["URL"]
main_df = main_df[main_cols]

# Normalize URLs
main_df["url_match"] = main_df["URL"].apply(normalize_url)
engage_df["url_match"] = engage_df["Url"].apply(normalize_url)


pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', None)

# print("Main URLs (first 50):")
# print(main_df[["url_match"]].head(50))
# print("Engagement URLs (first 50):")
# print(engage_df[["url_match"]].head(50))


# Merge
merged = main_df.merge(engage_df.drop(columns=["Url"]), how="left", on="url_match")

# print("Merged sample (first 50):")
# print(merged[["URL", "url_match", "PageViews", "PVMoM", "Visitors", "Engagement"]].head(50))

# Diagnostics: show unmatched URLs
unmatched = merged[merged["PageViews"].isna()]
print(f"\nUnmatched URLs in main file (first 50): {len(unmatched)}")
print(unmatched[["url_match"]].head(50))

matched = merged[~merged["PageViews"].isna()]
# print(f"\nMatched URLs in main file (first 50): {len(matched)}")
# print(matched[["url_match", "PageViews", "PVMoM", "Visitors", "Engagement"]].head(50))

# Save merged output for inspection
merged.to_csv("c:/git/toc-tools/test-engagement-merge.csv", index=False)
print("Merged output saved to test-engagement-merge.csv")
