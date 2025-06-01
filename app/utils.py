import hashlib
import secrets
import string
from typing import Dict, Any
from datetime import datetime, timedelta
import re
from jinja2 import Template, TemplateError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.data_upload.models import UploadedData


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


def validate_template_variables(template_variables: list, data_columns: list) -> tuple[bool, str]:
    """Validate that data columns match template variables."""
    required_vars = [var["name"] for var in template_variables if var.get("required", True)]
    
    missing_vars = set(required_vars) - set(data_columns)
    if missing_vars:
        return False, f"Missing required variables: {', '.join(missing_vars)}"
    
    return True, ""


def validate_data_types(row_data: Dict[str, Any], template_variables: list) -> tuple[bool, str]:
    """Validate data types against template variable definitions."""
    for var_def in template_variables:
        var_name = var_def["name"]
        var_type = var_def["type"]
        
        if var_name in row_data:
            value = row_data[var_name]
            
            if var_type == "string":
                if not isinstance(value, str):
                    return False, f"Variable '{var_name}' should be string, got {type(value).__name__}"
            elif var_type == "number":
                if not isinstance(value, (int, float)):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        return False, f"Variable '{var_name}' should be number, got {type(value).__name__}"
            elif var_type == "date":
                if not isinstance(value, datetime):
                    # Try to parse as date string
                    try:
                        datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                    except ValueError:
                        return False, f"Variable '{var_name}' should be date, got {type(value).__name__}"
    
    return True, ""
