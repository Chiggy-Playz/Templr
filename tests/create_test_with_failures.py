"""
Simple test to demonstrate failed rows CSV functionality.
This creates a test CSV with some deliberately invalid data to trigger failures.
"""

from pathlib import Path

import pandas as pd


def create_test_data_with_failures():
    """Create test data with some rows that will deliberately fail validation."""

    # Create test data with mixed valid and invalid entries
    test_data = {
        "Name": [
            "John Doe",  # Valid
            "",  # Invalid - empty name
            "Jane Smith",  # Valid
            None,  # Invalid - null name
            "Bob Wilson",  # Valid
        ],
        "Email": [
            "john@example.com",  # Valid
            "jane@example.com",  # Valid
            "not-an-email",  # Invalid - bad email format
            "bob@example.com",  # Valid
            "alice@example.com",  # Valid
        ],
        "Outstanding_amount": [
            100.50,  # Valid
            200.75,  # Valid
            "not-a-number",  # Invalid - not numeric
            300.00,  # Valid
            -50.25,  # Valid (negative amounts might be allowed)
        ],
        "Date_due": [
            "2024-06-15",  # Valid
            "2024-07-20",  # Valid
            "2024-08-25",  # Valid
            "not-a-date",  # Invalid - bad date format
            "2024-09-30",  # Valid
        ],
    }

    df = pd.DataFrame(test_data)

    # Save to test file
    test_file = Path("tests/data/test_with_failures.csv")
    test_file.parent.mkdir(exist_ok=True)
    df.to_csv(test_file, index=False)

    print("✓ Created test file with mixed valid/invalid data:")
    print(f"  File: {test_file}")
    print(f"  Rows: {len(df)}")
    print("\nData preview:")
    print(df)

    print("\nExpected failures:")
    print("- Row 2: Empty name")
    print("- Row 4: Null name")
    print("- Row 3: Invalid email format")
    print("- Row 3: Non-numeric amount")
    print("- Row 4: Invalid date format")

    return test_file


if __name__ == "__main__":
    print("🧪 Creating test data for failed rows functionality...")
    file_path = create_test_data_with_failures()
    print(f"\n📁 Test file created: {file_path}")
    print("\n📝 Next steps:")
    print("1. Upload this file through the web interface")
    print("2. Check that some rows fail validation")
    print("3. Verify both result CSV and failed rows CSV are created")
    print("4. Download both files to verify content")
