#!/usr/bin/env bash
# Disabled by default: this repository must not solicit promotion or perform
# authenticated account writes from a session-start hook.
#
# The historical implementation checked and added a GitHub star. It has been
# intentionally neutralized. Keep this file as a compatibility entry point for
# installations that still reference it.
set -euo pipefail

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
