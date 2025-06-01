#!/usr/bin/env python3
"""
Test script to verify comprehensive error handling in background data processing
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from pathlib import Path
import tempfile

from app.utils import (
    make_json_serializable_with_context,
    map_data_row,
    validate_template_variables,
)
import pandas as pd


def test_error_handling():
    """Test various error scenarios that the background processor should handle gracefully"""

    # Define template variables
    template_variables = [
        {"name": "name", "type": "string", "required": True, "aliases": []},
        {"name": "address", "type": "string", "required": True, "aliases": []},
        {"name": "amount", "type": "number", "required": True, "aliases": []},
    ]

    print("=== Testing Error Handling Scenarios ===")

    # Test 1: Valid data with NaN values
    print("\n1. Testing valid data with NaN values:")
    df_with_nan = pd.DataFrame(
        {
            "name": ["John Doe", "Jane Smith", "Bob Wilson"],
            "address": ["123 Main St", float("nan"), "789 Pine Rd"],  # NaN in address
            "amount": [1000.50, 2500.00, float("nan")],  # NaN in amount
        }
    )

    print(f"DataFrame with NaN:\n{df_with_nan}")
    print(f"NaN values: {df_with_nan.isnull().sum().to_dict()}")

    # Test processing each row
    data_columns = df_with_nan.columns.tolist()

    for index, (_, row) in enumerate(df_with_nan.iterrows()):
        print(f"\nProcessing row {index + 1}:")
        row_data = row.to_dict()
        print(f"  Raw data: {row_data}")

        # Map data
        mapped_data = map_data_row(row_data, template_variables, data_columns)
        print(f"  Mapped data: {mapped_data}")

        # Convert to JSON serializable
        try:
            serializable_data = make_json_serializable_with_context(mapped_data, template_variables)
            print(f"  Serializable data: {serializable_data}")

            # Test JSON serialization
            import json

            json_string = json.dumps(serializable_data)
            print(f"  JSON serialization successful: {len(json_string)} chars")

        except Exception as e:
            print(f"  Error processing row: {e}")

    # Test 2: Invalid file format
    print("\n2. Testing invalid file scenarios:")

    # Create a text file that's not CSV/Excel
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is not a CSV file")
        invalid_file = Path(f.name)

    print(f"Invalid file: {invalid_file}")

    # Test 3: Empty CSV
    print("\n3. Testing empty CSV:")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("")  # Empty file
        empty_file = Path(f.name)

    # Test 4: CSV with missing required columns
    print("\n4. Testing CSV with missing required columns:")
    df_missing_cols = pd.DataFrame(
        {
            "name": ["John Doe"],
            "address": ["123 Main St"],
            # Missing 'amount' column
        }
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df_missing_cols.to_csv(f.name, index=False)
        missing_cols_file = Path(f.name)

    # Test validation
    is_valid, error_msg = validate_template_variables(template_variables, df_missing_cols.columns.tolist())
    print(f"  Validation result: {is_valid}, Error: {error_msg}")

    # Test 5: CSV with invalid data types
    print("\n5. Testing CSV with invalid data types:")
    df_invalid_types = pd.DataFrame(
        {"name": ["John Doe"], "address": ["123 Main St"], "amount": ["not_a_number"]}  # Invalid number
    )

    print(f"DataFrame with invalid types:\n{df_invalid_types}")

    # Try to process the invalid data
    try:
        row_data = df_invalid_types.iloc[0].to_dict()
        mapped_data = map_data_row(row_data, template_variables, df_invalid_types.columns.tolist())
        serializable_data = make_json_serializable_with_context(mapped_data, template_variables)
        print(f"  Surprisingly processed: {serializable_data}")
    except Exception as e:
        print(f"  Expected error: {e}")

    # Clean up temporary files
    try:
        invalid_file.unlink()
        empty_file.unlink()
        missing_cols_file.unlink()
    except:
        pass

    print("\n=== Error Handling Test Completed ===")
    return True


if __name__ == "__main__":
    success = test_error_handling()
    if not success:
        sys.exit(1)
