# Tests Directory

This directory contains all test files and test data for the FastAPI Templr application's variable mapping and alias functionality.

## Test Files

### Core Functionality Tests

- **`test_comprehensive.py`** - Comprehensive test suite with pytest-style tests for variable mapping, data type validation, and JSON serialization
- **`test_variable_mapping.py`** - Basic variable mapping functionality tests
- **`test_json_serialization.py`** - Tests for JSON serialization of pandas Timestamps and other non-serializable objects

### Database and Migration Tests

- **`check_database.py`** - Utility to check if aliases are properly saved in the database
- **`migrate_aliases.py`** - Migration script to add aliases field to existing templates

### Test Runner

- **`run_tests.py`** - Main test runner that executes all test files and provides a summary

## Test Data

The `data/` directory contains sample CSV files for testing:

- **`test_data.csv`** - Standard CSV with exact column names matching template variables
- **`test_data_aliases.csv`** - CSV with column names that match through aliases
- **`test_data_mixed_case.csv`** - CSV with mixed case column names to test case-insensitive matching

## Running Tests

### Run All Tests

```bash
cd tests
python run_tests.py
```

### Run Individual Tests

```bash
cd tests
python test_comprehensive.py
python test_variable_mapping.py
python test_json_serialization.py
```

### Check Database State

```bash
cd tests
python check_database.py
```

### Run Migration (if needed)

```bash
cd tests
python migrate_aliases.py
```

## Test Coverage

The tests cover the following functionality:

### Variable Mapping

- ✅ Exact name matching
- ✅ Alias matching
- ✅ Case-insensitive matching
- ✅ Mixed case and alias combinations
- ✅ Validation of required variables
- ✅ Data row mapping with column transformation

### Data Type Validation

- ✅ String validation and conversion
- ✅ Number validation and conversion (int/float)
- ✅ Date validation and conversion
- ✅ Error handling for invalid data types

### JSON Serialization

- ✅ Basic dictionary serialization
- ✅ Pandas Timestamp conversion to ISO strings
- ✅ Python datetime conversion to ISO strings
- ✅ Nested dictionary serialization
- ✅ List serialization with mixed data types

### Database Integration

- ✅ Alias field persistence in database
- ✅ Template variable structure validation
- ✅ Migration support for existing templates

## Expected Behavior

### Variable Mapping Examples

Template variable: `outstanding_amount` with aliases: `["Outstanding_amount", "outstanding-amount", "OutstandingAmount"]`

CSV columns that should match:

- `outstanding_amount` (exact match)
- `Outstanding_amount` (alias match)
- `OUTSTANDING_AMOUNT` (case-insensitive exact match)
- `OutstandingAmount` (alias match)
- `outstanding-amount` (alias match)
- `OUTSTANDINGAMOUNT` (case-insensitive alias match)

### Data Type Conversion Examples

- String `"1500.50"` → Float `1500.50` (for number fields)
- String `"1500"` → Integer `1500` (for number fields)
- String `"2025-06-01"` → Datetime object (for date fields)
- Pandas Timestamp → ISO string `"2025-06-01T00:00:00"` (for JSON storage)

## Notes

- All tests should pass before deploying changes
- The test data files can be used for manual testing of the web interface
- Database tests require a running database connection
- Migration scripts should only be run once per database schema change
