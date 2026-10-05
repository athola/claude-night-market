#!/usr/bin/env bash
# Install egregore watchdog as a macOS launchd agent
set -euo pipefail

INTERVAL="${1:-300}"
WATCHDOG_SCRIPT="$(cd "$(dirname "$0")" && pwd)/watchdog.sh"
WORKING_DIR="${2:-$(pwd)}"
PLIST_NAME="com.egregore.watchdog"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Plist values are XML text. bash 5.2+ reads & in a replacement as the
# matched text unless patsub_replacement is off. bash 3.2 has no such
# option, so the shopt fails there and is ignored.
xml_escape() {
  shopt -u patsub_replacement 2>/dev/null || true
  local s="$1"
  s="${s//&/&amp;}"
  s="${s//</&lt;}"
  s="${s//>/&gt;}"
  printf '%s' "$s"
}

if [[ ! -f "$WATCHDOG_SCRIPT" ]]; then
  echo "Error: watchdog.sh not found at $WATCHDOG_SCRIPT"
  exit 1
fi

XML_SCRIPT="$(xml_escape "$WATCHDOG_SCRIPT")"
XML_DIR="$(xml_escape "$WORKING_DIR")"

cat >"$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${XML_SCRIPT}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${XML_DIR}</string>
    <key>StartInterval</key>
    <integer>${INTERVAL}</integer>
    <key>StandardOutPath</key>
    <string>${XML_DIR}/.egregore/watchdog-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>${XML_DIR}/.egregore/watchdog-launchd.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

GUI_DOMAIN="gui/$(id -u)"
# bootstrap refuses a label that is already loaded, so a re-install kept
# the old job. Unload it first; failure here means it was not loaded.
launchctl bootout "$GUI_DOMAIN/$PLIST_NAME" 2>/dev/null || true
if launchctl bootstrap "$GUI_DOMAIN" "$PLIST_PATH"; then
  : # modern macOS (10.10+)
else
  launchctl load "$PLIST_PATH" # fallback for older macOS
fi
echo "Installed: $PLIST_PATH"
echo "Checking every ${INTERVAL}s in ${WORKING_DIR}"
echo "To uninstall: launchctl bootout $GUI_DOMAIN/$PLIST_NAME 2>/dev/null || launchctl unload $PLIST_PATH; rm $PLIST_PATH"
