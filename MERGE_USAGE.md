# Excel Merge Functions Usage Guide

The `utils.excel_utils` module provides two functions for merging Excel data:

## 1. `merge_external_data()` - Legacy Pipeline Function
This is the existing function used by the pipeline, configured through environment variables.

```python
from utils.excel_utils import merge_external_data
df = merge_external_data(df, config)
```

## 2. `merge_excel_data()` - Generic Reusable Function  
This is the new generic function for flexible Excel data merging.

### Basic Usage

```python
from utils.excel_utils import merge_excel_data

# Basic merge (new columns always appear at beginning for better visibility)
df_merged = merge_excel_data(
    df=my_dataframe,
    excel_file_path="path/to/file.xlsx", 
    key_column="URL",
    merge_columns=["URL", "Notes", "Status", "Priority"]
)

# Advanced usage with all options
df_merged = merge_excel_data(
    df=my_dataframe,
    excel_file_path="path/to/file.xlsx",
    key_column="filename", 
    merge_columns="filename,status,priority,assigned_to",  # String format OK too
    sheet_name="Sheet1",
    debug=True
)
```

### Parameters
- `df`: DataFrame to merge data into
- `excel_file_path`: Path to Excel file
- `key_column`: Column name for matching (e.g., 'URL', 'filename')
- `merge_columns`: List or comma-separated string of columns to merge
- `sheet_name`: Excel sheet name (optional, uses first sheet if None)
- `debug`: Enable debug logging

### Key Features
- **Smart positioning**: New columns always appear at the beginning for better visibility
- **Multiple key columns**: Use any column for matching (URL, filename, ID, etc.)
- **Format flexibility**: Merge columns as list `['col1', 'col2']` or string `"col1,col2"`
- **Safe merging**: Automatically handles missing files, columns, or duplicate keys
- **Column conflict resolution**: Drops existing columns before merge to avoid conflicts

### Use Cases

1. **Pipeline Integration** (existing behavior):
   ```python
   df = merge_external_data(df, config)  # Uses environment variables
   ```

2. **Ad-hoc Analysis** (new columns at start):
   ```python  
   df = merge_excel_data(df, "analysis.xlsx", "URL", "URL,Notes,Priority", position="start")
   ```

3. **Multiple File Sources**:
   ```python
   # First merge from planning file
   df = merge_excel_data(df, "planning.xlsx", "filename", ["filename", "status", "owner"])
   
   # Then merge from review file  
   df = merge_excel_data(df, "reviews.xlsx", "URL", ["URL", "rating", "comments"])
   ```

### Column Positioning Examples

New columns are always positioned at the very beginning for maximum visibility:

```
Original: [URL, filename, title, author]
Result:   [Notes, Status, Priority, URL, filename, title, author]
```

**Note**: New columns always appear first, regardless of the key column position.

### Error Handling
The function safely handles:
- Missing Excel files (returns original DataFrame)
- Missing columns in Excel (skips unavailable columns)
- Missing key column (returns original DataFrame)
- Excel read errors (logs error, returns original DataFrame)

All errors are logged but don't crash the process.