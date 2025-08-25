# Multi-stage Dockerfile for NGÜ Bibelvers-Sponsoring App
# Optimized for production deployment with minimal image size

# =============================================================================
# Stage 1: Build Dependencies
# =============================================================================
FROM python:3.12-slim as builder

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf-xlib-2.0-dev \
    libgtk-3-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production Runtime
# =============================================================================
FROM python:3.12-slim as production

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    libxml2 \
    libxslt1.1 \
    libffi8 \
    libjpeg62-turbo \
    libpng16-16 \
    libcairo2 \
    libpango-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libgtk-3-0 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r flaskgroup && \
    useradd -r -g flaskgroup -u 1000 flaskuser && \
    mkdir -p /app/{uploads,logs,certificates,flask_session,static,templates,data} && \
    chown -R flaskuser:flaskgroup /app

# Copy application code (this will be mounted in development)
COPY --chown=flaskuser:flaskgroup . .

# Set proper permissions
RUN chmod +x /app/*.py && \
    mkdir -p /app/flask_session /app/uploads /app/logs /app/certificates && \
    chmod 755 /app/flask_session /app/uploads /app/logs /app/certificates

# Switch to non-root user
USER flaskuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose Flask port
EXPOSE 5000

# Default command
CMD ["python", "app.py"]

# =============================================================================
# Stage 3: Database Initialization (separate service)
# =============================================================================
FROM production as db-init

# Switch back to root for installation
USER root

# Copy database initialization scripts
COPY --chown=flaskuser:flaskgroup init-scripts/ /app/init-scripts/
COPY --chown=flaskuser:flaskgroup data/ /app/data/

# Switch back to flaskuser
USER flaskuser

# Command for database initialization
CMD ["python", "/app/init-scripts/initialize_database.py"]

# =============================================================================
# Stage 4: Development (for local development)
# =============================================================================
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-flask \
    pytest-cov \
    flask-debugtoolbar \
    ipython \
    ipdb

# Install development system packages
RUN apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Switch back to flaskuser
USER flaskuser

# Set development environment
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Development command
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

# =============================================================================
# Stage 5: Testing (for CI/CD)
# =============================================================================
FROM development as testing

# Copy test files
COPY --chown=flaskuser:flaskgroup tests/ /app/tests/

# Set testing environment
ENV FLASK_ENV=testing
ENV TESTING=True

# Command for running tests
CMD ["pytest", "-v", "--cov=app", "--cov-report=html", "--cov-report=term"]

# =============================================================================
# Labels and Metadata
# =============================================================================
LABEL maintainer="Ulrich Probst <uli@familieprobst.org>"
LABEL description="NGÜ Bibelvers-Sponsoring App - Docker Container"
LABEL version="1.0.0"
LABEL project="harvard-cs50-final"

# Environment variables defaults (can be overridden)
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"
