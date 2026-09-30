# =============================================================================
# eRTMAC-NWIS Production Dockerfile — Multi-Stage Build (Phase 09)
# Optimized for: Security, size minimization, and reproducible builds
# =============================================================================

# --- Stage 1: Build dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Production runtime ---
FROM python:3.11-slim AS runtime

# Security: Run as non-root user
RUN groupadd -r nwis && useradd -r -g nwis -d /app -s /sbin/nologin nwis

# Install only runtime libraries (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY --chown=nwis:nwis . .

# Create data directories with proper permissions
RUN mkdir -p /app/data/processed /app/data/uploaded /app/data/quarantine /app/logs \
    && chown -R nwis:nwis /app/data /app/logs

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER nwis

# Expose application port
EXPOSE 8000

# Production entrypoint with proper worker configuration
# Workers = 2 * CPU cores + 1 (gunicorn recommendation)
# Use uvicorn directly for single-instance rig-side deployment
CMD ["uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--timeout-keep-alive", "65", \
     "--access-log", \
     "--log-level", "info"]
