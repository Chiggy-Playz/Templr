"""
Test script to validate failed rows CSV generation functionality.
"""

import asyncio
import os
from pathlib import Path
import sys
import traceback

import pandas as pd

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.data_upload.service import DataUploadService
from app.database import async_session_maker
from app.templates.service import TemplateService
from app.users.models import User
from app.users.service import UserService


async def test_failed_rows_functionality():
    """Test that failed rows are properly captured and saved to CSV."""

    try:
        print("Starting failed rows test...")

        # Create test CSV with mixed valid and invalid data
        test_data = {
            "name": [
                "John Doe",
                "Jane Smith",
                "",
                "Bob Wilson",
                None,
            ],  # Some empty names
            "email": [
                "john@test.com",
                "invalid-email",
                "jane@test.com",
                "bob@test.com",
                "alice@test.com",
            ],  # One invalid email
            "Outstanding_amount": [
                100.50,
                "invalid-amount",
                200.75,
                300.00,
                150.25,
            ],  # One invalid amount
            "Date_due": [
                "2024-01-15",
                "2024-02-20",
                "invalid-date",
                "2024-03-10",
                "2024-04-05",
            ],  # One invalid date
        }

        test_df = pd.DataFrame(test_data)
        test_file_path = Path("tests/data/test_mixed_valid_invalid.csv")
        test_file_path.parent.mkdir(exist_ok=True)
        test_df.to_csv(test_file_path, index=False)

        print(f"Created test file with {len(test_df)} rows (mixed valid/invalid data)")
        print(f"Test data:")
        print(test_df)

        # Setup database session
        session = async_session_maker()

        try:
            # Get or create test user
            user_service = UserService(session)
            try:
                user = await user_service.get_user_by_email("test@example.com")
            except:
                # Create test user
                from app.users.schemas import UserCreate

                user_create = UserCreate(
                    email="test@example.com", password="testpass123"
                )
                user = await user_service.create_user(user_create)

            # Get or create test template
            template_service = TemplateService(session)
            try:
                template = await template_service.get_template_by_slug("test-template")
            except:
                # Create test template with validation
                from app.templates.schemas import TemplateCreate

                template_create = TemplateCreate(
                    name="Test Template",
                    slug="test-template",
                    variables=[
                        {
                            "name": "name",
                            "type": "text",
                            "aliases": ["Name"],
                            "required": True,
                        },
                        {
                            "name": "email",
                            "type": "email",
                            "aliases": ["Email"],
                            "required": True,
                        },
                        {
                            "name": "outstandingamount",
                            "type": "currency",
                            "aliases": ["Outstanding_amount"],
                            "required": True,
                        },
                        {
                            "name": "datedue",
                            "type": "date",
                            "aliases": ["Date_due"],
                            "required": True,
                        },
                    ],
                    content="Name: {{ name }}, Email: {{ email }}, Amount: {{ outstandingamount }}, Due: {{ datedue }}",
                )
                template = await template_service.create_template(template_create, user)

            print(f"Using template: {template.slug}")

            # Process the file directly using the service logic
            # data_service = DataUploadService(session)

            # Read the file
            df = pd.read_csv(test_file_path)
            print(f"Read file with {len(df)} rows")

            # Simulate the processing logic
            processed_data = []
            data_columns = df.columns.tolist()
            failed_rows = []

            print(f"Data columns: {data_columns}")
            print(f"Template variables: {[v['name'] for v in template.variables]}")

            # Check the processing loop logic
            df_with_index = df.reset_index(drop=True)

            for index, (original_index, row) in enumerate(df_with_index.iterrows()):
                row_data = {}
                try:
                    row_data = row.to_dict()

                    # Import the mapping and validation functions
                    from app.utils import (
                        make_json_serializable_with_context,
                        map_data_row,
                        validate_data_types,
                    )

                    # Map the row data to template variable names
                    mapped_data = map_data_row(
                        row_data, template.variables, data_columns
                    )

                    # Validate data types against template variables
                    is_valid, error_msg = validate_data_types(
                        mapped_data, template.variables
                    )
                    if not is_valid:
                        raise ValueError(f"Validation error: {error_msg}")

                    # Make data JSON serializable
                    serializable_data = make_json_serializable_with_context(
                        mapped_data, template.variables
                    )

                    # Add to processed data with original row order preserved
                    processed_row = serializable_data.copy()
                    processed_row["_original_row_index"] = original_index

                    processed_data.append(processed_row)
                    print(f"✓ Row {index + 1} processed successfully")

                except Exception as row_error:
                    print(f"✗ Row {index + 1} failed: {str(row_error)}")

                    # Create detailed failed row record with original data preserved
                    failed_row_record = row_data.copy()
                    failed_row_record["_row_number"] = index + 1
                    failed_row_record["_original_row_index"] = original_index
                    failed_row_record["_error_reason"] = str(row_error)
                    failed_row_record["_error_type"] = type(row_error).__name__

                    failed_rows.append(failed_row_record)

            print("\nProcessing summary:")
            print(f"Input rows: {len(df)}")
            print(f"Successfully processed: {len(processed_data)}")
            print(f"Failed rows: {len(failed_rows)}")

            # Create result files to test the CSV generation
            if processed_data:
                result_df = pd.DataFrame(processed_data)
                result_file = Path("tests/data/test_result_with_failures.csv")
                result_df.to_csv(result_file, index=False)
                print(f"✓ Result file saved: {result_file}")

            if failed_rows:
                failed_df = pd.DataFrame(failed_rows)
                failed_file = Path("tests/data/test_failed_rows.csv")
                failed_df.to_csv(failed_file, index=False)
                print(f"✓ Failed rows file saved: {failed_file}")
                print("\nFailed rows details:")
                print(
                    failed_df[
                        [
                            "_row_number",
                            "_error_reason",
                            "name",
                            "email",
                            "Outstanding_amount",
                            "Date_due",
                        ]
                    ]
                )
            else:
                print("No failed rows to save")

        finally:
            await session.close()

    except Exception as e:
        print(f"Error in test_failed_rows_functionality: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_failed_rows_functionality())
