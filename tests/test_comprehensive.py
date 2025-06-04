#!/usr/bin/env python3
"""
Comprehensive test suite for the variable mapping and alias functionality
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from app.utils import (
    create_variable_mapping,
    make_json_serializable,
    map_data_row,
    validate_data_types,
    validate_template_variables,
)
import pandas as pd


class TestVariableMapping:
    """Test class for variable mapping functionality"""

    @pytest.fixture
    def template_variables(self):
        """Sample template variables with aliases"""
        return [
            {
                "name": "customer_name",
                "type": "string",
                "required": True,
                "aliases": ["Customer_Name", "customerName", "Customer Name"],
            },
            {
                "name": "outstanding_amount",
                "type": "number",
                "required": True,
                "aliases": [
                    "Outstanding_amount",
                    "outstanding-amount",
                    "OutstandingAmount",
                    "Outstanding Amount",
                ],
            },
            {
                "name": "due_date",
                "type": "date",
                "required": True,
                "aliases": ["Due_Date", "due-date", "DueDate", "Due Date"],
            },
            {
                "name": "optional_field",
                "type": "string",
                "required": False,
                "aliases": ["opt_field", "OptionalField"],
            },
        ]

    def test_exact_match_mapping(self, template_variables):
        """Test mapping with exact variable names"""
        csv_columns = ["customer_name", "outstanding_amount", "due_date"]
        mapping = create_variable_mapping(template_variables, csv_columns)

        expected = {
            "customer_name": "customer_name",
            "outstanding_amount": "outstanding_amount",
            "due_date": "due_date",
        }
        assert mapping == expected

    def test_alias_mapping(self, template_variables):
        """Test mapping with aliases"""
        csv_columns = ["Customer_Name", "Outstanding_amount", "Due_Date"]
        mapping = create_variable_mapping(template_variables, csv_columns)

        expected = {
            "Customer_Name": "customer_name",
            "Outstanding_amount": "outstanding_amount",
            "Due_Date": "due_date",
        }
        assert mapping == expected

    def test_case_insensitive_mapping(self, template_variables):
        """Test case-insensitive mapping"""
        csv_columns = ["CUSTOMER_NAME", "outstanding_amount", "DueDate"]
        mapping = create_variable_mapping(template_variables, csv_columns)

        expected = {
            "CUSTOMER_NAME": "customer_name",
            "outstanding_amount": "outstanding_amount",
            "DueDate": "due_date",
        }
        assert mapping == expected

    def test_mixed_alias_case_mapping(self, template_variables):
        """Test mapping with mixed case aliases"""
        csv_columns = ["customerName", "OutstandingAmount", "due-date"]
        mapping = create_variable_mapping(template_variables, csv_columns)

        expected = {
            "customerName": "customer_name",
            "OutstandingAmount": "outstanding_amount",
            "due-date": "due_date",
        }
        assert mapping == expected

    def test_validation_success(self, template_variables):
        """Test successful validation"""
        csv_columns = ["Customer_Name", "Outstanding_amount", "Due_Date"]
        is_valid, error_msg = validate_template_variables(
            template_variables, csv_columns
        )

        assert is_valid == True
        assert error_msg == ""

    def test_validation_missing_required(self, template_variables):
        """Test validation with missing required variables"""
        csv_columns = ["Customer_Name", "Outstanding_amount"]  # Missing due_date
        is_valid, error_msg = validate_template_variables(
            template_variables, csv_columns
        )

        assert is_valid == False
        assert "due_date" in error_msg.lower()

    def test_data_row_mapping(self, template_variables):
        """Test mapping of data rows"""
        csv_columns = ["Customer_Name", "Outstanding_amount", "Due_Date"]
        sample_row = {
            "Customer_Name": "John Doe",
            "Outstanding_amount": "1500.50",
            "Due_Date": "2025-07-01",
        }

        mapped_row = map_data_row(sample_row, template_variables, csv_columns)

        expected = {
            "customer_name": "John Doe",
            "outstanding_amount": "1500.50",
            "due_date": "2025-07-01",
        }
        assert mapped_row == expected


class TestDataTypeValidation:
    """Test class for data type validation"""

    @pytest.fixture
    def template_variables(self):
        """Sample template variables for type testing"""
        return [
            {"name": "name", "type": "string", "required": True, "aliases": []},
            {"name": "amount", "type": "number", "required": True, "aliases": []},
            {"name": "date_field", "type": "date", "required": True, "aliases": []},
        ]

    def test_string_validation_success(self, template_variables):
        """Test successful string validation"""
        row_data = {"name": "John Doe", "amount": 100.0, "date_field": datetime.now()}
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == True
        assert error_msg == ""

    def test_number_conversion_success(self, template_variables):
        """Test successful number conversion"""
        row_data = {
            "name": "John Doe",
            "amount": "100.50",
            "date_field": datetime.now(),
        }
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == True
        assert error_msg == ""
        assert isinstance(row_data["amount"], float)
        assert row_data["amount"] == 100.50

    def test_integer_conversion_success(self, template_variables):
        """Test successful integer conversion"""
        row_data = {"name": "John Doe", "amount": "100", "date_field": datetime.now()}
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == True
        assert error_msg == ""
        assert isinstance(row_data["amount"], int)
        assert row_data["amount"] == 100

    def test_date_conversion_success(self, template_variables):
        """Test successful date conversion"""
        row_data = {"name": "John Doe", "amount": 100.0, "date_field": "2025-06-01"}
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == True
        assert error_msg == ""
        assert isinstance(row_data["date_field"], datetime)

    def test_invalid_number_validation(self, template_variables):
        """Test invalid number validation"""
        row_data = {
            "name": "John Doe",
            "amount": "not_a_number",
            "date_field": datetime.now(),
        }
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == False
        assert "amount" in error_msg

    def test_invalid_date_validation(self, template_variables):
        """Test invalid date validation"""
        row_data = {"name": "John Doe", "amount": 100.0, "date_field": "not_a_date"}
        is_valid, error_msg = validate_data_types(row_data, template_variables)

        assert is_valid == False
        assert "date_field" in error_msg


class TestJSONSerialization:
    """Test class for JSON serialization functionality"""

    def test_basic_dict_serialization(self):
        """Test basic dict serialization"""
        data = {"name": "John", "age": 30}
        result = make_json_serializable(data)

        assert result == data
        assert isinstance(result, dict)

    def test_pandas_timestamp_serialization(self):
        """Test pandas Timestamp serialization"""
        data = {"name": "John", "created_at": pd.Timestamp("2025-06-01")}
        result = make_json_serializable(data)

        assert result["name"] == "John"
        assert isinstance(result["created_at"], str)
        assert "2025-06-01" in result["created_at"]

    def test_datetime_serialization(self):
        """Test datetime serialization"""
        data = {"name": "John", "created_at": datetime(2025, 6, 1, 12, 30, 45)}
        result = make_json_serializable(data)

        assert result["name"] == "John"
        assert isinstance(result["created_at"], str)
        assert result["created_at"] == "2025-06-01T12:30:45"

    def test_nested_dict_serialization(self):
        """Test nested dict serialization"""
        data = {
            "user": {"name": "John", "created_at": pd.Timestamp("2025-06-01")},
            "metadata": {"last_login": datetime(2025, 6, 1, 10, 0, 0)},
        }
        result = make_json_serializable(data)

        assert result["user"]["name"] == "John"
        assert isinstance(result["user"]["created_at"], str)
        assert isinstance(result["metadata"]["last_login"], str)

    def test_list_serialization(self):
        """Test list serialization"""
        data = [{"date": pd.Timestamp("2025-06-01")}, {"date": datetime(2025, 6, 2)}]
        result = make_json_serializable(data)

        assert len(result) == 2
        assert isinstance(result[0]["date"], str)
        assert isinstance(result[1]["date"], str)


def run_all_tests():
    """Run all tests manually without pytest"""
    print("=== Running Variable Mapping Tests ===")

    # Create test instances
    mapping_tests = TestVariableMapping()
    validation_tests = TestDataTypeValidation()
    json_tests = TestJSONSerialization()

    # Get fixtures
    template_vars = mapping_tests.template_variables()
    validation_vars = validation_tests.template_variables()

    # Run mapping tests
    try:
        mapping_tests.test_exact_match_mapping(template_vars)
        print("✓ Exact match mapping test passed")

        mapping_tests.test_alias_mapping(template_vars)
        print("✓ Alias mapping test passed")

        mapping_tests.test_case_insensitive_mapping(template_vars)
        print("✓ Case insensitive mapping test passed")

        mapping_tests.test_mixed_alias_case_mapping(template_vars)
        print("✓ Mixed alias case mapping test passed")

        mapping_tests.test_validation_success(template_vars)
        print("✓ Validation success test passed")

        mapping_tests.test_validation_missing_required(template_vars)
        print("✓ Validation missing required test passed")

        mapping_tests.test_data_row_mapping(template_vars)
        print("✓ Data row mapping test passed")

    except Exception as e:
        print(f"✗ Mapping test failed: {e}")

    # Run validation tests
    try:
        validation_tests.test_string_validation_success(validation_vars)
        print("✓ String validation test passed")

        validation_tests.test_number_conversion_success(validation_vars)
        print("✓ Number conversion test passed")

        validation_tests.test_integer_conversion_success(validation_vars)
        print("✓ Integer conversion test passed")

        validation_tests.test_date_conversion_success(validation_vars)
        print("✓ Date conversion test passed")

        validation_tests.test_invalid_number_validation(validation_vars)
        print("✓ Invalid number validation test passed")

        validation_tests.test_invalid_date_validation(validation_vars)
        print("✓ Invalid date validation test passed")

    except Exception as e:
        print(f"✗ Validation test failed: {e}")

    # Run JSON tests
    try:
        json_tests.test_basic_dict_serialization()
        print("✓ Basic dict serialization test passed")

        json_tests.test_pandas_timestamp_serialization()
        print("✓ Pandas timestamp serialization test passed")

        json_tests.test_datetime_serialization()
        print("✓ Datetime serialization test passed")

        json_tests.test_nested_dict_serialization()
        print("✓ Nested dict serialization test passed")

        json_tests.test_list_serialization()
        print("✓ List serialization test passed")

    except Exception as e:
        print(f"✗ JSON serialization test failed: {e}")

    print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    run_all_tests()
