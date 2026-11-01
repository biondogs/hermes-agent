# hermes-upstream — always-fresh upstream Hermes image
# Reuses the board-layers harness Dockerfile; same deps, same isolation.
# Build context is the upstream clone (hermes-board-layers/).
FROM python:3.14-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    HERMES_HOME=/tmp/hermes-home \
    HERMES_RUNTIME_DIR=/tmp/hermes-runtime \
    TZ=UTC \
    LANG=C.UTF-8 \
    PYTHONHASHSEED=0

RUN apt-get update && apt-get install -y --no-install-recommends \
        git sqlite3 curl procps \
    && apt-get clean \
    && pip install --upgrade pip wheel setuptools -q

WORKDIR /opt/hermes

COPY pyproject.toml ./
RUN python3 -c "import tomllib,subprocess,sys; d=tomllib.load(open('pyproject.toml','rb')); deps=[x for x in d['project']['dependencies'] if 'browser-harness' not in x and 'browser_harness' not in x]; subprocess.run([sys.executable,'-m','pip','install','-q',*deps], check=False)" \
 && pip install -q pytest 2>&1 | tail -3 || true

# Entrypoint is needed for run-branch; scripts are optional (only on feat branches)
COPY dev/board-layers-harness/entrypoint.sh /usr/local/bin/harness-entrypoint
RUN chmod +x /usr/local/bin/harness-entrypoint

ENTRYPOINT ["harness-entrypoint"]
CMD ["bash"]
