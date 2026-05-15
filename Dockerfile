FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

CMD ["uv", "run", "sh", "-c", "python manage.py collectstatic --noinput && gunicorn choosy.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
