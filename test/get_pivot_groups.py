#!/usr/bin/env python3

import pandas as pd

# Read the CSV properly
df = pd.read_csv('foundry-toc-metadata.csv')

# Get all unique pivot groups
pivot_groups = df[df['pivot_groups'] != '']['pivot_groups'].dropna()

# Split comma-separated values and collect all unique individual pivot IDs
all_pivots = set()
for group_str in pivot_groups:
    if isinstance(group_str, str) and group_str.strip():
        pivots = [p.strip() for p in group_str.split(',')]
        all_pivots.update(pivots)

print("Unique pivot group values:")
for pivot in sorted(all_pivots):
    print(f"  {pivot}")

print(f"\nTotal unique pivot groups: {len(all_pivots)}")
