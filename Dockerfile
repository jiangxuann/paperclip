# Multi-stage Dockerfile for Paperclip (uv-based)
FROM python:3.11-slim AS base

# Common environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install base runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# ----------------------------
# Builder stage
# ----------------------------
FROM base AS builder

# Build deps for common compiled wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project metadata first for better layer caching
COPY pyproject.toml ./

# Resolve and install dependencies into a local project venv (.venv)
RUN uv sync --no-dev

# Copy rest of the application source
COPY . .

# Ensure the local project itself is installed into the environment
RUN uv sync --no-dev

# ----------------------------
# Production stage
# ----------------------------
FROM base AS production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PDF processing
    poppler-utils \
    # Video processing
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r paperclip && useradd -r -g paperclip paperclip

WORKDIR /app

# Copy the venv and source from builder (use correct ownership)
COPY --from=builder --chown=paperclip:paperclip /app/.venv /app/.venv
COPY --from=builder --chown=paperclip:paperclip /app /app

# Ensure the venv is preferred for all commands
ENV PATH="/app/.venv/bin:$PATH" \
    ENVIRONMENT=production

# Create necessary directories
RUN mkdir -p uploads output temp logs && \
    chown -R paperclip:paperclip uploads output temp logs

# Switch to non-root user
USER paperclip

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Expose ports for API and UI
EXPOSE 8000 8501

# Default command: run API via uv and the synced environment
CMD ["uv", "run", "-m", "api.main"]
