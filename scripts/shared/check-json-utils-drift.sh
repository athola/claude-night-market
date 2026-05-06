#!/usr/bin/env bash
# Verify vendored JSON utilities match scripts/shared/json_utils.sh.
#
# Each plugin keeps a byte-identical copy of json_utils.sh under
# hooks/shared/ so its hooks can source via
# ${CLAUDE_PLUGIN_ROOT}/hooks/shared/json_utils.sh from the Claude
# Code plugin cache. This script enforces that those vendored
# copies stay byte-identical to the canonical.
#
# Exit codes:
#   0 - all vendored copies match the canonical
#   1 - drift detected (one or more vendored copies differ)
#   2 - usage / file-not-found error

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CANONICAL="${REPO_ROOT}/scripts/shared/json_utils.sh"

VENDORED=(
    "plugins/imbue/hooks/shared/json_utils.sh"
    "plugins/conserve/hooks/shared/json_utils.sh"
    "plugins/memory-palace/hooks/shared/json_utils.sh"
)

if [[ ! -f "$CANONICAL" ]]; then
    echo "ERROR: canonical not found: $CANONICAL" >&2
    exit 2
fi

drift=0
for vendored in "${VENDORED[@]}"; do
    vendored_path="${REPO_ROOT}/${vendored}"
    if [[ ! -f "$vendored_path" ]]; then
        echo "ERROR: vendored copy missing: $vendored" >&2
        drift=1
        continue
    fi
    if ! diff -q "$CANONICAL" "$vendored_path" >/dev/null 2>&1; then
        echo "DRIFT: $vendored differs from $CANONICAL"
        diff "$CANONICAL" "$vendored_path" || true
        drift=1
    fi
done

if (( drift )); then
    echo ""
    echo "ERROR: vendored JSON utilities have drifted from canonical." >&2
    echo "Re-run: cp scripts/shared/json_utils.sh <each vendored path>" >&2
    exit 1
fi

echo "OK: all vendored JSON utilities match canonical."
