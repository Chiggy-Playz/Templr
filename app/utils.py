from datetime import date, datetime, timedelta
import hashlib
import json
import math
import re
import secrets
import string
from typing import Any, Dict, List, Union

from app.data_upload.models import UploadedData
from jinja2 import Template, TemplateError
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def generate_unique_identifier(data: Dict[str, Any], min_length: int = 8) -> str:
    """Generate a unique identifier based on data content."""
    # Create a hash from the data
    data_str = str(sorted(data.items()))
    hash_obj = hashlib.sha256(data_str.encode())
    hex_hash = hash_obj.hexdigest()

    # Start with minimum length and increase if needed for collision detection
    return hex_hash[:min_length]


async def ensure_unique_identifier(
    session: AsyncSession, data: Dict[str, Any], min_length: int = 8, max_length: int = 32
) -> str:
    """Ensure the identifier is unique in the database."""
    for length in range(min_length, max_length + 1):
        identifier = generate_unique_identifier(data, length)

        # Check if identifier already exists
        result = await session.execute(select(UploadedData).where(UploadedData.identifier == identifier))
        existing = result.scalar_one_or_none()

        if not existing:
            return identifier

    # If we can't find a unique identifier, add random suffix
    base_identifier = generate_unique_identifier(data, max_length - 4)
    random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{base_identifier}{random_suffix}"


def calculate_expiry_date() -> datetime:
    """Calculate expiry date (30 days from now)."""
    from datetime import timezone

    return datetime.now(timezone.utc) + timedelta(days=30)


def render_template(template_content: str, variables: Dict[str, Any]) -> str:
    """Render a Jinja2 template with the provided variables."""
    try:
        template = Template(template_content)
        return template.render(**variables)
    except TemplateError as e:
        raise ValueError(f"Template rendering error: {str(e)}")


def create_variable_mapping(template_variables: list, data_columns: list) -> Dict[str, str]:
    """Create mapping from data columns to template variables considering aliases and case-insensitive matching."""
    mapping = {}

    # Create a lookup for template variables with their aliases
    template_var_lookup = {}
    for var_def in template_variables:
        var_name = var_def["name"]
        aliases = var_def.get("aliases", [])

        # Add the variable name itself (case-insensitive)
        template_var_lookup[var_name.lower()] = var_name

        # Add all aliases (case-insensitive)
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                template_var_lookup[alias.lower()] = var_name

    # Match data columns to template variables
    for col in data_columns:
        col_lower = col.lower()
        if col_lower in template_var_lookup:
            mapping[col] = template_var_lookup[col_lower]

    return mapping


def validate_template_variables(template_variables: list, data_columns: list) -> tuple[bool, str]:
    """Validate that data columns match template variables with case-insensitive and alias support."""
    required_vars = [var["name"] for var in template_variables if var.get("required", True)]

    # Create mapping from data columns to template variables
    mapping = create_variable_mapping(template_variables, data_columns)

    # Check if all required variables are covered
    mapped_template_vars = set(mapping.values())
    missing_vars = set(required_vars) - mapped_template_vars

    if missing_vars:
        return False, f"Missing required variables: {', '.join(missing_vars)}"

    return True, ""


def map_data_row(row_data: Dict[str, Any], template_variables: list, data_columns: list) -> Dict[str, Any]:
    """Map data row using variable mapping to standardize column names."""
    mapping = create_variable_mapping(template_variables, data_columns)
    mapped_data = {}

    for col, value in row_data.items():
        if col in mapping:
            template_var = mapping[col]
            mapped_data[template_var] = value
        else:
            # Keep unmapped columns as-is
            mapped_data[col] = value

    return mapped_data


def validate_data_types(row_data: Dict[str, Any], template_variables: list) -> tuple[bool, str]:
    """Validate data types against template variable definitions."""
    for var_def in template_variables:
        var_name = var_def["name"]
        var_type = var_def["type"]

        if var_name in row_data:
            value = row_data[var_name]

            # Skip validation for empty/null values
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue

            if var_type == "string":
                if not isinstance(value, str):
                    # Convert to string if possible
                    try:
                        row_data[var_name] = str(value)
                    except Exception:
                        return False, f"Variable '{var_name}' should be string, got {type(value).__name__}"
            elif var_type == "number":
                if not isinstance(value, (int, float)):
                    try:
                        # Try to convert to number
                        if isinstance(value, str):
                            if "." in value:
                                row_data[var_name] = float(value)
                            else:
                                row_data[var_name] = int(value)
                        else:
                            row_data[var_name] = float(value)
                    except (ValueError, TypeError):
                        return False, f"Variable '{var_name}' should be number, got invalid value: {value}"
            elif var_type == "date":
                if not isinstance(value, datetime):
                    # Try to parse as date string
                    try:
                        if isinstance(value, str):
                            parsed_date = datetime.fromisoformat(value.replace("Z", "+00:00"))
                            row_data[var_name] = parsed_date
                        else:
                            return False, f"Variable '{var_name}' should be date, got {type(value).__name__}"
                    except ValueError:
                        return False, f"Variable '{var_name}' should be date, got invalid format: {value}"

    return True, ""


def make_json_serializable(data: Any, var_type: Union[str, None] = None) -> Any:
    """
    Convert data to JSON serializable format.
    Handles pandas Timestamps, datetime objects, NaN values, and other non-serializable types.

    NaN imputation rules:
    - For string fields: empty string ""
    - For numeric fields: -1
    - For datetime fields: epoch start (1970-01-01T00:00:00)
    """
    # Handle NaN values first (they can come from pandas or numpy)
    if _is_nan_value(data):
        return _impute_nan_value(var_type)

    if isinstance(data, dict):
        return {key: make_json_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(item) for item in data]
    elif hasattr(data, "isoformat"):  # datetime, date, pandas Timestamp
        return data.isoformat()
    elif hasattr(data, "to_pydatetime"):  # pandas Timestamp
        return data.to_pydatetime().isoformat()
    elif hasattr(data, "item"):  # numpy scalars
        scalar_value = data.item()
        # Check if the scalar value is NaN
        if _is_nan_value(scalar_value):
            return _impute_nan_value(var_type)
        return scalar_value
    elif str(type(data)).startswith("<class 'pandas"):  # Other pandas types
        str_value = str(data)
        # Handle pandas NaN string representation
        if str_value in ("nan", "NaN", "<NA>"):
            return _impute_nan_value(var_type)
        return str_value
    else:
        # For basic types that are already JSON serializable
        return data


def make_template_ready(data: Any, var_type: Union[str, None] = None) -> Any:
    """
    Convert data to template-ready format, preserving datetime objects for template use.
    Similar to make_json_serializable but keeps datetime objects as datetime for Jinja2 templates.

    NaN imputation rules:
    - For string fields: empty string ""
    - For numeric fields: -1
    - For datetime fields: epoch start (1970-01-01T00:00:00)
    """
    # Handle NaN values first (they can come from pandas or numpy)
    if _is_nan_value(data):
        return _impute_nan_value(var_type)

    if isinstance(data, dict):
        return {key: make_template_ready(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_template_ready(item) for item in data]
    elif hasattr(data, "to_pydatetime"):  # pandas Timestamp - convert to datetime
        return data.to_pydatetime()
    elif isinstance(data, (datetime, date)):  # Keep datetime/date objects as-is
        return data
    elif hasattr(data, "item"):  # numpy scalars
        scalar_value = data.item()
        # Check if the scalar value is NaN
        if _is_nan_value(scalar_value):
            return _impute_nan_value(var_type)
        return scalar_value
    elif str(type(data)).startswith("<class 'pandas"):  # Other pandas types
        str_value = str(data)
        # Handle pandas NaN string representation
        if str_value in ("nan", "NaN", "<NA>"):
            return _impute_nan_value(var_type)
        return str_value
    else:
        # For basic types that are already template-ready
        return data


def _is_nan_value(data: Any) -> bool:
    """Check if a value is NaN in any form"""
    try:
        # Check for float NaN
        if isinstance(data, float) and math.isnan(data):
            return True
        # Check for numpy NaN
        if hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
            if np.isnan(data):
                return True  # Check for pandas NA
        try:
            import pandas as pd

            # Only check pandas.isna for supported types
            if not isinstance(data, (dict, list)):
                if pd.isna(data):
                    return True
        except ImportError:
            pass
        return False
    except (TypeError, ValueError):
        return False


def _impute_nan_value(var_type: Union[str, None] = None) -> Any:
    """Impute NaN values based on variable type"""
    if var_type == "string":
        return ""
    elif var_type == "number":
        return -1
    elif var_type == "date":
        return datetime(1970, 1, 1)  # Return actual datetime object
    else:
        # Default to empty string for unknown types
        return ""


def make_json_serializable_with_context(row_data: Dict[str, Any], template_variables: list) -> Dict[str, Any]:
    """
    Convert row data to JSON serializable format with variable type context.
    This version knows the expected data types and can properly impute NaN values.
    """
    # Create a lookup for variable types
    var_type_lookup = {}
    for var_def in template_variables:
        var_name = var_def["name"]
        var_type = var_def["type"]
        var_type_lookup[var_name] = var_type

    result = {}
    for key, value in row_data.items():
        var_type = var_type_lookup.get(key, None)
        result[key] = make_json_serializable(value, var_type)

    return result


def make_template_ready_with_context(row_data: Dict[str, Any], template_variables: list) -> Dict[str, Any]:
    """
    Convert row data to template-ready format with variable type context.
    This version preserves datetime objects for template rendering.
    """
    # Create a lookup for variable types
    var_type_lookup = {}
    for var_def in template_variables:
        var_name = var_def["name"]
        var_type = var_def["type"]
        var_type_lookup[var_name] = var_type

    result = {}
    for key, value in row_data.items():
        var_type = var_type_lookup.get(key, None)
        result[key] = make_template_ready(value, var_type)

    return result
