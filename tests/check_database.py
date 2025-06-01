#!/usr/bin/env python3
"""
Test script to verify alias functionality in database
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_maker
from app.templates.models import Template
from app.users.models import User
from app.data_upload.models import UploadedData, UploadJob  # Import all models to resolve relationships
from sqlalchemy import select

async def check_aliases_in_database():
    """Check if aliases are being saved in the database"""
    
    async with async_session_maker() as session:
        # Get all templates
        result = await session.execute(select(Template))
        templates = result.scalars().all()
        
        print("=== Database Template Analysis ===")
        print(f"Found {len(templates)} templates in database")
        print()
        
        for template in templates:
            print(f"Template: {template.name} (slug: {template.slug})")
            print(f"Variables: {len(template.variables)}")
            for i, var in enumerate(template.variables):
                print(f"  Variable {i+1}:")
                print(f"    Name: {var.get('name', 'N/A')}")
                print(f"    Type: {var.get('type', 'N/A')}")
                print(f"    Required: {var.get('required', 'N/A')}")
                
                # Check for aliases field specifically
                if 'aliases' in var:
                    aliases = var['aliases']
                    print(f"    Aliases: {aliases} (type: {type(aliases)})")
                else:
                    print(f"    Aliases: No aliases field")
                print()
            
            print(f"Raw variables data: {template.variables}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(check_aliases_in_database())
