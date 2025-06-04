#!/usr/bin/env python3
"""
Migration script to add aliases field to existing templates
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_maker
from app.templates.models import Template
from sqlalchemy import select


async def migrate_aliases():
    """Add empty aliases arrays to existing template variables"""

    async with async_session_maker() as session:
        # Get all templates
        result = await session.execute(select(Template))
        templates = result.scalars().all()

        print(f"Found {len(templates)} templates to migrate")

        for template in templates:
            print(f"Migrating template: {template.name}")

            # Check if any variables are missing the aliases field
            modified = False
            for var in template.variables:
                if "aliases" not in var:
                    var["aliases"] = []
                    modified = True
                    print(
                        f"  Added aliases field to variable: {var.get('name', 'unnamed')}"
                    )

            if modified:
                # Mark the template as modified to trigger the update
                template.variables = template.variables.copy()
                session.add(template)
                print(f"  Template {template.name} marked for update")

        # Commit all changes
        await session.commit()
        print("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_aliases())
