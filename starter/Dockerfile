FROM python:3.11-slim

WORKDIR /app/starter

# Install uv
RUN pip install uv

# Copy project files from starter directory
COPY starter/pyproject.toml ./
COPY starter/src ./src
COPY starter/tests ./tests
COPY starter/test_runtime.py ./

# Install dependencies
RUN uv sync

# Copy data directory
COPY data /app/data

# Run tests by default
CMD ["uv", "run", "pytest", "-v"]
