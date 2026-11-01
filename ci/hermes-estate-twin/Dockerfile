# hermes-estate-twin Dockerfile
# Lightweight twin harness: Python 3.14 + hermes-agent deps.
# NO estate data is baked — twin-root is bind-mounted at runtime.
# Reuses the same debian trixie base the live image uses.
FROM debian:trixie-20261020@sha256:4c25275446ca371766b8b093c696782eabce06263fccacb8d5d813b3dc44b308

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -o Acquire::Retries=3 update && \
    apt-get -o Acquire::Retries=3 install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        git rsync sqlite3 curl ca-certificates \
        build-essential pkg-config \
        libsqlite3-dev \
        ripgrep jq \
    && rm -rf /var/lib/apt/lists/*

# Install uv for hermes pm compatibility
RUN pip install --no-cache-dir --break-system-packages uv==0.11.3

# Create hermes user (matches host UID handling in compose)
RUN useradd -m -s /bin/bash hermes

# Copy hermes-agent source deps install
# We install from the bind-mounted source at runtime via entrypoint,
# but bake common deps for faster cold start.
WORKDIR /opt/twin

COPY sync/requirements-twin.txt /tmp/requirements-twin.txt
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements-twin.txt 2>&1 | tail -5 || true

COPY scripts/entrypoint.sh /usr/local/bin/twin-entrypoint.sh
RUN chmod +x /usr/local/bin/twin-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/twin-entrypoint.sh"]
CMD ["sleep", "infinity"]
