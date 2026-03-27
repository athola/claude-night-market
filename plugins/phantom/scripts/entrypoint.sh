#!/bin/bash
# Start virtual display and window manager for computer use
set -e

# Start Xvfb (virtual framebuffer)
Xvfb :1 -screen 0 1920x1080x24 &
sleep 1

# Start a lightweight window manager
mutter --replace --display=:1 &
sleep 1

# Start panel
tint2 &

echo "Display environment ready on :1 (1920x1080)"
echo "Run tasks with: python -m phantom.cli <task>"

# If arguments provided, run them; otherwise keep alive
if [ $# -gt 0 ]; then
    exec "$@"
else
    exec bash
fi
