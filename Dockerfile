# Multi-stage Dockerfile for Paperclip
# Optimized for production deployment with minimal image size

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY pyproject.toml /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    cd /tmp && \
    pip install -e .

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    # PDF processing
    poppler-utils \
    # Video processing
    ffmpeg \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r paperclip && useradd -r -g paperclip paperclip

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application code
COPY --chown=paperclip:paperclip . .

# Create necessary directories
RUN mkdir -p uploads output temp logs && \
    chown -R paperclip:paperclip uploads output temp logs

# Switch to non-root user
USER paperclip

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose ports
EXPOSE 8000 8501

# Default command
CMD ["python", "-m", "api.main"]
