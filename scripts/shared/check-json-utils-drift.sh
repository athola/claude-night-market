#!/usr/bin/env bash
# Verify inlined JSON utilities match scripts/shared/json_utils.sh
#
# Several plugin hooks intentionally inline get_json_field and
# escape_for_json to avoid broken relative paths when the plugin runs
# from Claude Code's cache. The hooks carry a "do not DRY-refactor"
# comment but no enforcement. This script provides the enforcement.
#
# Exit codes:
#   0 - all inlined copies match the canonical
#   1 - drift detected (one or more inlined copies differ)
#   2 - usage / file-not-found error

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CANONICAL="${REPO_ROOT}/scripts/shared/json_utils.sh"

CONSUMERS=(
    "plugins/imbue/hooks/session-start.sh"
    "plugins/conserve/hooks/session-start.sh"
)

if [[ ! -f "$CANONICAL" ]]; then
    echo "ERROR: canonical not found: $CANONICAL" >&2
    exit 2
fi

# Extract a function body from a shell file. Matches lines from
# `<name>() {` through the next top-level `}` (a `}` at column 1).
# Strips standalone comment lines so drift detection focuses on
# executable logic; consumer copies may legitimately omit comments.
extract_fn() {
    local file="$1" fn="$2"
    awk -v fn="$fn" '
        index($0, fn"() {") == 1 { in_fn = 1 }
        in_fn { print }
        in_fn && $0 == "}" { in_fn = 0 }
    ' "$file" \
        | grep -v '^[[:space:]]*#' \
        | grep -v '^[[:space:]]*$' \
        | sed 's/;;[[:space:]]*#.*$/;;/'
}

drift=0
for fn in get_json_field escape_for_json; do
    canonical_body="$(extract_fn "$CANONICAL" "$fn")"
    if [[ -z "$canonical_body" ]]; then
        echo "ERROR: '$fn' not found in $CANONICAL" >&2
        exit 2
    fi
    for consumer in "${CONSUMERS[@]}"; do
        consumer_path="${REPO_ROOT}/${consumer}"
        if [[ ! -f "$consumer_path" ]]; then
            echo "WARN: consumer not found: $consumer (skipping)" >&2
            continue
        fi
        consumer_body="$(extract_fn "$consumer_path" "$fn")"
        if [[ -z "$consumer_body" ]]; then
            echo "WARN: '$fn' not inlined in $consumer (skipping)" >&2
            continue
        fi
        if [[ "$canonical_body" != "$consumer_body" ]]; then
            echo "DRIFT: $consumer / $fn differs from $CANONICAL"
            diff <(printf '%s\n' "$canonical_body") \
                 <(printf '%s\n' "$consumer_body") || true
            drift=1
        fi
    done
done

if (( drift )); then
    echo ""
    echo "ERROR: inlined JSON utilities have drifted from canonical." >&2
    echo "Update consumers to match $CANONICAL or update the canonical and consumers together." >&2
    exit 1
fi

echo "OK: all inlined JSON utilities match canonical."
