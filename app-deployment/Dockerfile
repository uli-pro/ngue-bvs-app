# =============================================================================
# NGÜ BVS App - Production Dockerfile
# =============================================================================
# Multi-stage build for optimized image size and security
# Stage 1: Builder - compiles dependencies
# Stage 2: Production - minimal runtime environment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
# Note: WeasyPrint requires specific system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    # Add production server
    pip install gunicorn==21.2.0

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    # Flask configuration
    FLASK_ENV=production \
    FLASK_DEBUG=0

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client
    libpq5 \
    # WeasyPrint runtime dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    shared-mime-info \
    # Font packages for PDF generation
    fonts-liberation \
    fonts-dejavu-core \
    # Health check
    curl \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f -v

# Copy Python environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r flaskapp && \
    useradd -r -g flaskapp -u 1000 flaskapp && \
    mkdir -p /app /app/flask_session /app/logs /app/certificates /app/uploads && \
    chown -R flaskapp:flaskapp /app

# Set working directory
WORKDIR /app

# Copy application code (respects .dockerignore)
# ⚠️ WICHTIG: Neue .py Dateien müssen in .dockerignore Whitelist!
COPY --chown=flaskapp:flaskapp . .

# Create required directories if they don't exist
RUN mkdir -p static/certificates templates && \
    chown -R flaskapp:flaskapp /app

# Switch to non-root user
USER flaskapp

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose port (documentation only, not binding)
EXPOSE 5000

# Use exec form for proper signal handling
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "3", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]
