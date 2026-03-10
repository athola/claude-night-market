#!/usr/bin/env bash
# Install egregore watchdog as a systemd user timer
set -euo pipefail

INTERVAL="${1:-5}"
WATCHDOG_SCRIPT="$(cd "$(dirname "$0")" && pwd)/watchdog.sh"
WORKING_DIR="${2:-$(pwd)}"
UNIT_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="egregore-watchdog"

mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Egregore Watchdog Service

[Service]
Type=oneshot
WorkingDirectory=${WORKING_DIR}
ExecStart=${WATCHDOG_SCRIPT}
EOF

cat > "$UNIT_DIR/${SERVICE_NAME}.timer" << EOF
[Unit]
Description=Egregore Watchdog Timer

[Timer]
OnBootSec=${INTERVAL}min
OnUnitActiveSec=${INTERVAL}min

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now "${SERVICE_NAME}.timer"
echo "Installed: ${SERVICE_NAME}.timer"
echo "Checking every ${INTERVAL}min in ${WORKING_DIR}"
echo "To uninstall: systemctl --user disable --now ${SERVICE_NAME}.timer"
