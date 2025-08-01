#!/usr/bin/env python3

import os

# Test the path resolution logic
base_path = "/Users/sherigilley/git/azure-ai-docs-pr/articles/ai-foundry"
href = "../ai-services/connect-services-ai-foundry-portal.md?context=/azure/ai-foundry/context/context"

print(f"Base path: {base_path}")
print(f"Original href: {href}")

# Test the current logic (what it was doing before)
full_path_old = os.path.normpath(os.path.join(base_path, href))
print(f"Old resolved path: {full_path_old}")
print(f"Old file exists: {os.path.exists(full_path_old)}")

# Test the new logic (with query parameter stripping)
href_clean = href.split('?')[0]
full_path_new = os.path.normpath(os.path.join(base_path, href_clean))
print(f"Clean href: {href_clean}")
print(f"New resolved path: {full_path_new}")
print(f"New file exists: {os.path.exists(full_path_new)}")
