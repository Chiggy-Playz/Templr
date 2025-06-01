# Variable Matching and Aliases Documentation

## Overview

The template system now supports case-insensitive variable matching and alias names for template variables. This allows for more flexible data mapping when uploading CSV/Excel files.

## Features

### 1. Case-Insensitive Variable Matching

- Template variables are matched case-insensitively with CSV column headers
- Example: Template variable `outstandingamount` will match CSV columns like:
  - `outstandingamount`
  - `OutstandingAmount`
  - `OUTSTANDINGAMOUNT`
  - `outstandingAmount`

### 2. Variable Aliases

- Each template variable can have multiple alias names
- Aliases are defined as comma-separated values when creating/editing templates
- Example: Variable `outstandingamount` with aliases:
  - `Outstanding_amount`
  - `outstanding-amount`
  - `OutstandingAmount`
  - `outstanding amount`

### 3. How It Works

#### Template Creation/Editing

1. When creating or editing a template, you can specify aliases for each variable
2. Enter aliases as comma-separated values in the "Aliases" field
3. Aliases are case-insensitive and will be matched accordingly

#### Data Upload Processing

1. When a CSV/Excel file is uploaded, the system creates a mapping between CSV columns and template variables
2. The mapping considers both the variable name and all its aliases (case-insensitive)
3. Data is then mapped to the standardized variable names before storage
4. Template rendering uses the standardized variable names

#### Example Workflow

1. Template variable: `outstandingamount`
2. Aliases: `Outstanding_amount, outstanding-amount, OutstandingAmount`
3. CSV column: `Outstanding_amount`
4. Result: CSV data is mapped to `outstandingamount` variable

## Benefits

- **Flexibility**: Accommodate different CSV file formats without requiring exact column name matches
- **Reusability**: Same template can work with CSV files from different sources with varying column naming conventions
- **User-Friendly**: Reduces the need to modify CSV files or create multiple templates for similar data structures

## Implementation Details

- Variable mapping is created during data validation
- Original CSV column names are preserved in processing but data is stored using standardized variable names
- Template rendering uses the standardized variable names ensuring consistency
