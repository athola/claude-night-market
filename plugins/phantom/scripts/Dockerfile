FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

# Install display tools and a lightweight desktop
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xdotool \
    scrot \
    xclip \
    mutter \
    tint2 \
    firefox \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip3 install uv

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

# Install phantom
RUN uv pip install --system .

# Start Xvfb and a basic window manager
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5900

ENTRYPOINT ["/entrypoint.sh"]
