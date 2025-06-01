"""
Test script to validate data processing - specifically checking for row loss and shuffling.
"""

import asyncio
import os
from pathlib import Path
import sys

import pandas as pd

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.data_upload.service import DataUploadService
from app.database import async_session_maker
from app.templates.service import TemplateService
from app.users.models import User
from app.users.service import UserService


async def test_data_processing():
    """Test that data processing preserves all rows and maintains order."""

    # Create test CSV with known data
    test_data = {
        "name": [f"Person {i}" for i in range(1, 555)],  # 554 rows
        "email": [f"person{i}@example.com" for i in range(1, 555)],
        "Outstanding_amount": [100 + i for i in range(1, 555)],
        "Date_due": ["2024-01-15" for _ in range(1, 555)],
    }

    test_df = pd.DataFrame(test_data)
    test_file_path = Path("tests/data/test_large_dataset.csv")
    test_file_path.parent.mkdir(exist_ok=True)
    test_df.to_csv(test_file_path, index=False)

    print(f"Created test file with {len(test_df)} rows")
    print(f"First few rows:")
    print(test_df.head())
    print(f"Last few rows:")
    print(test_df.tail())

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

            user_create = UserCreate(email="test@example.com", password="testpass123")
            user = await user_service.create_user(user_create)

        # Get or create test template
        template_service = TemplateService(session)
        try:
            template = await template_service.get_template_by_slug("test-template")
        except:
            # Create test template
            from app.templates.schemas import TemplateCreate

            template_create = TemplateCreate(
                name="Test Template",
                slug="test-template",
                variables=[
                    {"name": "name", "type": "text", "aliases": ["Name"]},
                    {"name": "email", "type": "email", "aliases": ["Email"]},
                    {
                        "name": "outstandingamount",
                        "type": "currency",
                        "aliases": ["Outstanding_amount", "outstanding-amount"],
                    },
                    {"name": "datedue", "type": "date", "aliases": ["Date_due", "date-due"]},
                ],
                content="Name: {{ name }}, Email: {{ email }}, Amount: {{ outstandingamount }}, Due: {{ datedue }}",
            )
            template = await template_service.create_template(template_create, user)

        print(f"Using template: {template.slug}")

        # Process the file directly using the service logic
        data_service = DataUploadService(session)

        # Read the file
        df = pd.read_csv(test_file_path)
        print(f"Read file with {len(df)} rows")

        # Simulate the processing logic
        processed_data = []
        data_columns = df.columns.tolist()

        print(f"Data columns: {data_columns}")
        print(f"Template variables: {[v['name'] for v in template.variables]}")

        # Check the processing loop logic
        df_with_index = df.reset_index(drop=True)

        for index, (original_index, row) in enumerate(df_with_index.iterrows()):
            try:
                row_data = row.to_dict()

                # Import the mapping function
                from app.utils import make_json_serializable_with_context, map_data_row

                # Map the row data to template variable names
                mapped_data = map_data_row(row_data, template.variables, data_columns)

                # Make data JSON serializable
                serializable_data = make_json_serializable_with_context(mapped_data, template.variables)

                # Add to processed data with original row order preserved
                processed_row = serializable_data.copy()
                processed_row["_original_row_index"] = original_index

                processed_data.append(processed_row)

                if index < 5 or index >= len(df) - 5:  # Show first and last few
                    print(f"Row {index + 1} (original {original_index}): {processed_row}")

            except Exception as e:
                print(f"Error processing row {index + 1}: {e}")

        print(f"\nProcessing complete:")
        print(f"Input rows: {len(df)}")
        print(f"Output rows: {len(processed_data)}")
        print(f"Missing rows: {len(df) - len(processed_data)}")

        # Create result DataFrame and check order
        if processed_data:
            result_df = pd.DataFrame(processed_data)
            print(f"Result DataFrame shape: {result_df.shape}")
            print(f"Columns: {list(result_df.columns)}")

            # Check if original order is preserved
            if "_original_row_index" in result_df.columns:
                original_indices = result_df["_original_row_index"].tolist()
                expected_indices = list(range(len(result_df)))
                print(f"Original indices (first 10): {original_indices[:10]}")
                print(f"Expected indices (first 10): {expected_indices[:10]}")
                print(f"Order preserved: {original_indices == expected_indices}")

            # Save result file
            result_file = Path("tests/data/processing_result.csv")
            result_df.to_csv(result_file, index=False)
            print(f"Result saved to: {result_file}")

        else:
            print("No data was processed!")

    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(test_data_processing())
