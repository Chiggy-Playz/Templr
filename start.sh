#!/bin/sh
echo "Running Alembic migrations..."
uv run alembic upgrade head

echo "Starting app..."
uv run -m app