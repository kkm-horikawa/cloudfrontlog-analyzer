# Backend Dockerfile for CloudFront Analyzer
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user with same UID as host user
ARG UID=1000
ARG GID=1000
RUN groupadd -g ${GID} appuser 2>/dev/null || true && \
    useradd -m -u ${UID} -g ${GID} appuser 2>/dev/null || \
    useradd -m -u ${UID} appuser 2>/dev/null || true

# Set working directory and change ownership BEFORE installing deps
WORKDIR /app
RUN chown ${UID}:${GID} /app

# Switch to non-root user BEFORE installing dependencies
USER ${UID}

# Copy dependency files and install as non-root
COPY --chown=${UID}:${GID} pyproject.toml .
RUN uv sync --no-dev

# Copy application code
COPY --chown=${UID}:${GID} . .

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "uv run --no-dev python manage.py migrate && uv run --no-dev python manage.py runserver 0.0.0.0:8000"]
