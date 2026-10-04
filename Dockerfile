# syntax=docker/dockerfile:1.7
FROM python:3.14-slim-trixie AS builder

# Pin uv; use a digest as well when your deployment requires immutable inputs.
COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

WORKDIR /app
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

# Resolve and install third-party dependencies in a cacheable layer.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock,readonly \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml,readonly \
    uv sync --locked --no-dev --no-install-project --no-editable

COPY . /app

# Install the packaged application non-editably for deployment.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.14-slim-trixie

# scapy compiles BPF filters through libpcap. The file capabilities let the non-root user capture
# packets, but the kernel then refuses to start Python unless the container is given both
# capabilities: run it with `--cap-add NET_RAW --cap-add NET_ADMIN`.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcap0.8t64 libcap2-bin \
    && setcap cap_net_raw,cap_net_admin+eip "$(readlink -f /usr/local/bin/python3.14)" \
    && apt-get purge -y libcap2-bin \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --system --uid 10001 --create-home --home-dir /home/nmtds nmtds \
    && mkdir /data \
    && chown nmtds /data

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" \
    NMTDS_HOST=0.0.0.0 \
    NMTDS_DATA_DIR=/data
WORKDIR /app
USER nmtds
VOLUME /data
EXPOSE 8000

# Migrate in a short-lived CLI process, then hand PID 1 to a server that never loads the CLI
# or alembic (about 12 MiB less for the long-running process).
CMD ["/bin/sh", "-c", "nmtds db upgrade && exec python -m network_monitor_tds.server"]

