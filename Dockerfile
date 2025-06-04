# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy Alembic configuration
COPY alembic.ini .

COPY start.sh /start.sh

RUN chmod +x /start.sh

# Copy only the app directory
COPY app ./app

EXPOSE 8000

CMD ["/start.sh"]