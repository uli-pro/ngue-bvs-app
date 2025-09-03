# Multi-stage Dockerfile for NGÜ Bibelvers-Sponsoring App
FROM python:3.12-slim as builder

ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev libxml2-dev libxslt1-dev libffi-dev \
    libjpeg-dev libpng-dev libcairo2-dev libpango1.0-dev \
    libgdk-pixbuf-2.0-0 libgtk-3-dev \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim as production

ARG DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies including gdk-pixbuf
RUN apt-get update && apt-get install -y \
    libpq5 libxml2 libxslt1.1 libffi8 \
    libjpeg62-turbo libpng16-16 libcairo2 \
    libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libgobject-2.0-0 libgtk-3-0 \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create non-root user
RUN groupadd -r flaskgroup && \
    useradd -r -g flaskgroup -u 1000 flaskuser && \
    mkdir -p /app/uploads /app/logs /app/certificates /app/flask_session /app/static /app/templates && \
    chown -R flaskuser:flaskgroup /app

# Copy application
COPY --chown=flaskuser:flaskgroup . .

# Set permissions
RUN chmod +x /app/*.py 2>/dev/null || true && \
    chmod 755 /app/flask_session /app/uploads /app/logs /app/certificates

USER flaskuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]