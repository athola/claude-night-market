#!/usr/bin/env bash
# Start virtual display and window manager for computer use
set -euo pipefail

# Start Xvfb (virtual framebuffer). -displayfd makes it write the display
# number once it accepts clients; a dead Xvfb (a stale /tmp/.X1-lock, say)
# stops the entrypoint instead of running the task against no display.
ready_file="$(mktemp)"
Xvfb :1 -screen 0 1920x1080x24 -displayfd 3 3>"${ready_file}" &
xvfb_pid=$!
tries=0
until [ -s "${ready_file}" ]; do
    if ! kill -0 "${xvfb_pid}" 2>/dev/null; then
        echo "Xvfb exited before display :1 was ready" >&2
        exit 1
    fi
    tries=$((tries + 1))
    if [ "${tries}" -gt 100 ]; then
        echo "Xvfb was not ready on :1 after 10s" >&2
        exit 1
    fi
    sleep 0.1
done
rm -f "${ready_file}"

# Start a lightweight window manager
mutter --replace --display=:1 &
sleep 1

# Start panel
tint2 &

echo "Display environment ready on :1 (1920x1080)"
echo "Run tasks with: python -m phantom.cli <task>"

# If arguments provided, run them; otherwise keep alive
if [ "$#" -gt 0 ]; then
    exec "$@"
else
    exec bash
fi
