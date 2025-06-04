#!/usr/bin/env python3
"""
Test script to verify NaN handling in data upload processing
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import make_json_serializable_with_context, map_data_row
import pandas as pd


def test_nan_handling():
    """Test NaN handling in the upload process"""

    # Define template variables matching the legal template
    template_variables = [
        {"name": "name", "type": "string", "required": True, "aliases": []},
        {"name": "address", "type": "string", "required": True, "aliases": []},
        {"name": "legal_date", "type": "date", "required": True, "aliases": []},
        {"name": "loan_amount", "type": "number", "required": True, "aliases": []},
        {"name": "loan_id", "type": "string", "required": True, "aliases": []},
        {"name": "outstanding_amount", "type": "number", "required": True, "aliases": []},
        {"name": "authorised_representative", "type": "string", "required": True, "aliases": []},
    ]

    # Read test CSV with NaN values
    csv_path = "tests/data/test_data_with_nan.csv"
    df = pd.read_csv(csv_path)

    print("=== Testing NaN Handling in Upload Process ===")
    print(f"Original DataFrame:\n{df}")
    print("\nDataFrame info:")
    print(df.info())
    print("\nNaN values per column:")
    print(df.isnull().sum())

    data_columns = df.columns.tolist()
    print(f"\nData columns: {data_columns}")

    # Process each row like the upload service does
    for index, (_, row) in enumerate(df.iterrows()):
        print(f"\n--- Processing Row {index + 1} ---")
        row_data = row.to_dict()
        print(f"Raw row data: {row_data}")

        # Map data (though in this case columns match exactly)
        mapped_data = map_data_row(row_data, template_variables, data_columns)
        print(f"Mapped data: {mapped_data}")

        # Convert to JSON serializable with type context
        serializable_data = make_json_serializable_with_context(mapped_data, template_variables)
        print(f"Serializable data: {serializable_data}")

        # Test JSON serialization
        import json

        try:
            json_string = json.dumps(serializable_data)
            print(f"JSON serialization successful: {len(json_string)} characters")
        except Exception as e:
            print(f"JSON serialization failed: {e}")
            return False

    print("\n=== NaN Handling Test PASSED ===")
    return True


if __name__ == "__main__":
    success = test_nan_handling()
    if not success:
        sys.exit(1)
