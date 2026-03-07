#!/usr/bin/env bash
# Install egregore watchdog as a macOS launchd agent
set -euo pipefail

INTERVAL="${1:-300}"
WATCHDOG_SCRIPT="$(cd "$(dirname "$0")" && pwd)/watchdog.sh"
WORKING_DIR="${2:-$(pwd)}"
PLIST_NAME="com.egregore.watchdog"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

if [[ ! -f "$WATCHDOG_SCRIPT" ]]; then
    echo "Error: watchdog.sh not found at $WATCHDOG_SCRIPT"
    exit 1
fi

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${WATCHDOG_SCRIPT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${WORKING_DIR}</string>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>StandardOutPath</key>
    <string>${WORKING_DIR}/.egregore/watchdog-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${WORKING_DIR}/.egregore/watchdog-launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"
echo "Installed: $PLIST_PATH"
echo "Checking every ${INTERVAL}s in ${WORKING_DIR}"
echo "To uninstall: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
