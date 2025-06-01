import hashlib
import secrets
import string
from typing import Dict, Any, Union, List
from datetime import datetime, timedelta, date
import re
from jinja2 import Template, TemplateError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.data_upload.models import UploadedData
import json
from datetime import date


def generate_unique_identifier(data: Dict[str, Any], min_length: int = 8) -> str:
    """Generate a unique identifier based on data content."""
    # Create a hash from the data
    data_str = str(sorted(data.items()))
    hash_obj = hashlib.sha256(data_str.encode())
    hex_hash = hash_obj.hexdigest()
    
    # Start with minimum length and increase if needed for collision detection
    return hex_hash[:min_length]


async def ensure_unique_identifier(
    session: AsyncSession, 
    data: Dict[str, Any], 
    min_length: int = 8,
    max_length: int = 32
) -> str:
    """Ensure the identifier is unique in the database."""
    for length in range(min_length, max_length + 1):
        identifier = generate_unique_identifier(data, length)
        
        # Check if identifier already exists
        result = await session.execute(
            select(UploadedData).where(UploadedData.identifier == identifier)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            return identifier
    
    # If we can't find a unique identifier, add random suffix
    base_identifier = generate_unique_identifier(data, max_length - 4)
    random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{base_identifier}{random_suffix}"


def calculate_expiry_date() -> datetime:
    """Calculate expiry date (30 days from now)."""
    return datetime.utcnow() + timedelta(days=30)


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
                            if '.' in value:
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
                            parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            row_data[var_name] = parsed_date
                        else:
                            return False, f"Variable '{var_name}' should be date, got {type(value).__name__}"
                    except ValueError:
                        return False, f"Variable '{var_name}' should be date, got invalid format: {value}"
    
    return True, ""


def make_json_serializable(data: Any) -> Any:
    """
    Convert data to JSON serializable format.
    Handles pandas Timestamps, datetime objects, and other non-serializable types.
    """
    if isinstance(data, dict):
        return {key: make_json_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(item) for item in data]
    elif hasattr(data, 'isoformat'):  # datetime, date, pandas Timestamp
        return data.isoformat()
    elif hasattr(data, 'to_pydatetime'):  # pandas Timestamp
        return data.to_pydatetime().isoformat()
    elif hasattr(data, 'item'):  # numpy scalars
        return data.item()
    elif str(type(data)).startswith("<class 'pandas"):  # Other pandas types
        return str(data)
    else:
        # For basic types that are already JSON serializable
        return data
