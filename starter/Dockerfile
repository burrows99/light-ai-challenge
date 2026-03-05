FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests

# Install dependencies
RUN uv sync --system

# Copy data from parent directory
COPY ../data ./data

# Run tests by default
CMD ["uv", "run", "pytest", "-v"]
