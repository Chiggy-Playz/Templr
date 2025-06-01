#!/usr/bin/env python3
"""
Test script for JSON serialization functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import math
from datetime import datetime
from app.utils import make_json_serializable, make_json_serializable_with_context

def test_json_serialization():
    """Test the JSON serialization functionality"""
    
    # Create test data with problematic types including NaN
    test_data = {
        "name": "John Doe",
        "amount": 1500.50,
        "date_field": pd.Timestamp('2025-06-01'),
        "datetime_field": datetime(2025, 6, 1, 12, 30, 45),
        "nan_field": float('nan'),
        "numpy_nan": np.nan,
        "pandas_na": pd.NA,
        "nested_dict": {
            "another_date": pd.Timestamp('2025-07-01'),
            "regular_field": "test",
            "another_nan": float('nan')
        },
        "list_with_nan": [1, 2, float('nan'), 4]
    }
    
    print("=== Testing JSON Serialization with NaN Values ===")
    print(f"Original data keys: {list(test_data.keys())}")
    print(f"NaN field value: {test_data['nan_field']} (type: {type(test_data['nan_field'])})")
    print(f"NumPy NaN value: {test_data['numpy_nan']} (type: {type(test_data['numpy_nan'])})")
    
    # Test serialization
    serializable_data = make_json_serializable(test_data)
    print(f"Serialized data: {serializable_data}")
    print(f"NaN field after serialization: {serializable_data.get('nan_field')} (type: {type(serializable_data.get('nan_field'))})")
    
    # Test that it's actually JSON serializable
    import json
    try:
        json_string = json.dumps(serializable_data)
        print(f"JSON serialization successful: {len(json_string)} characters")
        
        # Test that we can deserialize it back
        deserialized = json.loads(json_string)
        print(f"Deserialization successful")
        print(f"NaN field in deserialized: {deserialized.get('nan_field')}")
        
        # Test context-aware serialization
        print("\n=== Testing Context-Aware Serialization ===")
        template_variables = [
            {"name": "name", "type": "string"},
            {"name": "amount", "type": "number"},
            {"name": "date_field", "type": "date"},
            {"name": "address", "type": "string"}
        ]
        
        row_data_with_nan = {
            "name": "John Doe",
            "amount": float('nan'),
            "date_field": pd.Timestamp('2025-06-01'),
            "address": np.nan
        }
        
        context_serialized = make_json_serializable_with_context(row_data_with_nan, template_variables)
        print(f"Context-aware serialized: {context_serialized}")
        
        # Test JSON serialization
        json_string_context = json.dumps(context_serialized)
        print(f"Context-aware JSON serialization successful: {len(json_string_context)} characters")
        
        return True
    except Exception as e:
        print(f"JSON serialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_json_serialization()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
