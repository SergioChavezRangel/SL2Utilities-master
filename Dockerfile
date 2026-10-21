# =====================================================================
# Build Stage
# =====================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies and package
COPY pyproject.toml setup.py README.md ./
COPY sl2util ./sl2util

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

# =====================================================================
# Runtime Stage
# =====================================================================
FROM python:3.12-slim AS runtime

LABEL maintainer="Sergio Chavez Rangel <l2.steel.automation@gmail.com>" \
      description="SL2Utilities Watchdog & Automation Runtime Container"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    WATCHDOG_PORT=65001 \
    WATCHDOG_NAME=sl2_watchdog

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/sl2util /app/sl2util

# Create dedicated non-root user and log directory
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser && \
    mkdir -p /app/log && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 65001

# Container healthcheck querying the TCP watchdog heartbeat
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket, sys; s = socket.socket(); s.settimeout(2); s.connect(('127.0.0.1', int('$WATCHDOG_PORT'))); res = s.recv(1024); sys.exit(0 if b'RUN' in res else 1)"

ENTRYPOINT ["sl2util-watchdog"]
CMD ["--host", "0.0.0.0", "--port", "65001"]
