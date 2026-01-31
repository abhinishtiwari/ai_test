# Soulene Server - Dockerfile
# Multi-stage build for optimized production image

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 soulene && \
    chown -R soulene:soulene /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/soulene/.local

# Copy application code
COPY --chown=soulene:soulene soulene_server.py .
COPY --chown=soulene:soulene chat_interface.html .

# Switch to non-root user
USER soulene

# Add local bin to PATH
ENV PATH=/home/soulene/.local/bin:$PATH

# Environment variables (override with -e or .env)
ENV GOOGLE_API_KEY="" \
    FLASK_PORT=5000 \
    FLASK_HOST=0.0.0.0 \
    DEBUG_MODE=False \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "soulene_server.py"]
