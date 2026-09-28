#!/usr/bin/env bash
# Autonomous relaunch is disabled by default.
# Explicit opt-in is required because this script can start Claude without a
# fresh interactive user request and may consume external tools or providers.
set -euo pipefail

if [[ "${EGREGORE_WATCHDOG_ENABLE:-}" != "1" ]]; then
  exit 0
fi

printf '%s\n' 'Egregore watchdog is disabled in the sanitized distribution.' >&2
exit 1
