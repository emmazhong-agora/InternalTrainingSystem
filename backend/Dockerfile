# Multi-stage build for optimized production image
FROM docker.m.daocloud.io/library/python:3.11-slim-bookworm as builder
ARG DEBIAN_APT_MIRROR

# Set working directory
WORKDIR /app

# Install system dependencies
RUN if [ -n "$DEBIAN_APT_MIRROR" ]; then \
        if [ -f /etc/apt/sources.list ]; then \
            sed -i "s|http://deb.debian.org|https://${DEBIAN_APT_MIRROR}|g" /etc/apt/sources.list && \
            sed -i "s|http://security.debian.org|https://${DEBIAN_APT_MIRROR}|g" /etc/apt/sources.list; \
        fi; \
        if [ ! -f /etc/apt/sources.list ]; then \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm main contrib non-free-firmware" > /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm-updates main contrib non-free-firmware" >> /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm-backports main contrib non-free-firmware" >> /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian-security bookworm-security main contrib non-free-firmware" >> /etc/apt/sources.list; \
        fi; \
    fi && \
    apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim-bookworm

# FROM docker.m.daocloud.io/library/python:3.11-slim-bookworm
ARG DEBIAN_APT_MIRROR

WORKDIR /app

# Install runtime dependencies
RUN if [ -n "$DEBIAN_APT_MIRROR" ]; then \
        if [ -f /etc/apt/sources.list ]; then \
            sed -i "s|http://deb.debian.org|https://${DEBIAN_APT_MIRROR}|g" /etc/apt/sources.list && \
            sed -i "s|http://security.debian.org|https://${DEBIAN_APT_MIRROR}|g" /etc/apt/sources.list; \
        fi; \
        if [ ! -f /etc/apt/sources.list ]; then \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm main contrib non-free-firmware" > /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm-updates main contrib non-free-firmware" >> /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian bookworm-backports main contrib non-free-firmware" >> /etc/apt/sources.list && \
            echo "deb https://${DEBIAN_APT_MIRROR}/debian-security bookworm-security main contrib non-free-firmware" >> /etc/apt/sources.list; \
        fi; \
    fi && \
    apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /opt/venv /opt/venv

# Make sure scripts in .local are usable
ENV PATH=/opt/venv/bin:$PATH

# Copy application code
COPY . .

# Create directory for ChromaDB persistence
RUN mkdir -p /app/chroma_db

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /opt/venv

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
