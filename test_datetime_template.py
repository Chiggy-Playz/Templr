#!/usr/bin/env python3
"""
Quick test to verify datetime objects are properly passed to templates
"""
from datetime import datetime
from app.utils import make_template_ready_with_context, make_json_serializable_with_context

# Sample template variables
template_variables = [
    {"name": "name", "type": "string"},
    {"name": "amount", "type": "number"},
    {"name": "created_at", "type": "date"},
]

# Sample row data with datetime
test_data = {"name": "John Doe", "amount": 1000.50, "created_at": datetime(2025, 6, 1, 14, 30, 0)}

print("Original data:")
print(f"created_at type: {type(test_data['created_at'])}")
print(f"created_at value: {test_data['created_at']}")

# Test JSON serialization (for database storage)
json_ready = make_json_serializable_with_context(test_data, template_variables)
print("\nJSON serializable (for database):")
print(f"created_at type: {type(json_ready['created_at'])}")
print(f"created_at value: {json_ready['created_at']}")

# Test template-ready format (preserves datetime objects)
template_ready = make_template_ready_with_context(test_data, template_variables)
print("\nTemplate ready (preserves datetime):")
print(f"created_at type: {type(template_ready['created_at'])}")
print(f"created_at value: {template_ready['created_at']}")

# Test template rendering with datetime object
from app.utils import render_template

template_content = """
<p>Name: {{ name }}</p>
<p>Amount: ${{ amount }}</p>
<p>Created: {{ created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
<p>Year: {{ created_at.year }}</p>
<p>Month: {{ created_at.month }}</p>
"""

try:
    rendered = render_template(template_content, template_ready)
    print("\nTemplate rendered successfully:")
    print(rendered)
except Exception as e:
    print(f"\nTemplate rendering error: {e}")
