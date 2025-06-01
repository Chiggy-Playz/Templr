#!/usr/bin/env python3
"""
Test script for variable mapping functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import create_variable_mapping, validate_template_variables, map_data_row


def test_variable_mapping():
    """Test the variable mapping functionality"""

    # Define template variables with aliases
    template_variables = [
        {
            "name": "customer_name",
            "type": "string",
            "required": True,
            "aliases": ["Customer_Name", "customerName", "Customer Name"],
        },
        {
            "name": "outstandingamount",
            "type": "number",
            "required": True,
            "aliases": ["Outstanding_amount", "outstanding-amount", "OutstandingAmount", "Outstanding Amount"],
        },
        {
            "name": "duedate",
            "type": "date",
            "required": True,
            "aliases": ["Due_Date", "due-date", "DueDate", "Due Date"],
        },
    ]

    # Test CSV columns with different case and formats
    csv_columns = ["Customer_Name", "Outstanding_amount", "Due_Date"]

    print("=== Testing Variable Mapping ===")
    print(f"Template variables: {[var['name'] for var in template_variables]}")
    print(f"CSV columns: {csv_columns}")

    # Test mapping creation
    mapping = create_variable_mapping(template_variables, csv_columns)
    print(f"Generated mapping: {mapping}")

    # Test validation
    is_valid, error_msg = validate_template_variables(template_variables, csv_columns)
    print(f"Validation result: {is_valid}, Error: {error_msg}")

    # Test data row mapping
    sample_row = {"Customer_Name": "John Doe", "Outstanding_amount": "1500.50", "Due_Date": "2025-07-01"}

    mapped_row = map_data_row(sample_row, template_variables, csv_columns)
    print(f"Original row: {sample_row}")
    print(f"Mapped row: {mapped_row}")

    # Test case insensitive matching
    print("\n=== Testing Case Insensitive Matching ===")
    csv_columns_mixed_case = ["CUSTOMER_NAME", "outstanding_amount", "DueDate"]

    mapping2 = create_variable_mapping(template_variables, csv_columns_mixed_case)
    print(f"Mixed case CSV columns: {csv_columns_mixed_case}")
    print(f"Generated mapping: {mapping2}")

    # Test with aliases
    print("\n=== Testing Alias Matching ===")
    csv_columns_with_aliases = ["customerName", "OutstandingAmount", "due-date"]

    mapping3 = create_variable_mapping(template_variables, csv_columns_with_aliases)
    print(f"CSV columns with aliases: {csv_columns_with_aliases}")
    print(f"Generated mapping: {mapping3}")

    sample_row_aliases = {"customerName": "Jane Smith", "OutstandingAmount": "750.25", "due-date": "2025-06-15"}

    mapped_row_aliases = map_data_row(sample_row_aliases, template_variables, csv_columns_with_aliases)
    print(f"Original row with aliases: {sample_row_aliases}")
    print(f"Mapped row: {mapped_row_aliases}")


if __name__ == "__main__":
    test_variable_mapping()
