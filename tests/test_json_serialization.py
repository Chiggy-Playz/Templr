#!/usr/bin/env python3
"""
Test script for JSON serialization functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
from app.utils import make_json_serializable

def test_json_serialization():
    """Test the JSON serialization functionality"""
    
    # Create test data with problematic types
    test_data = {
        "name": "John Doe",
        "amount": 1500.50,
        "date_field": pd.Timestamp('2025-06-01'),
        "datetime_field": datetime(2025, 6, 1, 12, 30, 45),
        "nested_dict": {
            "another_date": pd.Timestamp('2025-07-01'),
            "regular_field": "test"
        }
    }
    
    print("=== Testing JSON Serialization ===")
    print(f"Original data: {test_data}")
    print(f"Data types: {[(k, type(v)) for k, v in test_data.items()]}")
    
    # Test serialization
    serializable_data = make_json_serializable(test_data)
    print(f"Serialized data: {serializable_data}")
    print(f"Serialized types: {[(k, type(v)) for k, v in serializable_data.items()]}")
    
    # Test that it's actually JSON serializable
    import json
    try:
        json_string = json.dumps(serializable_data)
        print(f"JSON serialization successful: {len(json_string)} characters")
        
        # Test that we can deserialize it back
        deserialized = json.loads(json_string)
        print(f"Deserialization successful: {deserialized}")
        
        return True
    except Exception as e:
        print(f"JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_json_serialization()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
