#!/usr/bin/env bash
# health-snapshot.sh: read-only repo health summary for claude-night-market.
#
# Runs the cheap, non-mutating diagnostic checks and prints a PASS/FAIL
# table. Failing checks dump their output to stderr so the table stays
# clean. Exit 0 when every check passes, 1 otherwise.
#
# Dependencies: bash, python3. No uv, no network, no writes.
#
# Usage:
#   bash .claude/skills/night-market-diagnostics-toolkit/scripts/health-snapshot.sh

set -u

# Script lives at .claude/skills/<skill>/scripts/; repo root is 4 levels up.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$REPO_ROOT" || exit 1

NAMES=()
RESULTS=()
overall=0

run_check() {
    local name="$1"
    shift
    local out rc
    out="$("$@" 2>&1)"
    rc=$?
    NAMES+=("$name")
    if [ "$rc" -eq 0 ]; then
        RESULTS+=("PASS")
    else
        RESULTS+=("FAIL")
        overall=1
        printf -- '--- %s failed (exit %d) ---\n%s\n\n' "$name" "$rc" "$out" >&2
    fi
}

validate_all_plugins() {
    local rc=0 p
    for p in plugins/*/; do
        [ -f "${p}.claude-plugin/plugin.json" ] || continue
        if ! python3 plugins/abstract/scripts/validate_plugin.py "${p%/}" \
            >/dev/null 2>&1; then
            echo "validate_plugin.py FAILED for ${p%/}"
            rc=1
        fi
    done
    return "$rc"
}

run_check "plugin-structure (validate_plugin.py, all plugins)" validate_all_plugins
run_check "capabilities-sync (docs vs registrations)" bash scripts/capabilities-sync-check.sh
run_check "supply-chain-scan (lockfile blocklist)" python3 scripts/supply_chain_scan.py
run_check "skill-graph-drift (ratchet)" python3 scripts/check_skill_graph_drift.py
run_check "exit-criteria-drift (ratchet)" python3 scripts/check_skill_exit_criteria_drift.py
run_check "description-budget (160-char / 90K ceiling)" python3 plugins/abstract/scripts/validate_budget.py

printf '\n%-50s %s\n' "CHECK" "RESULT"
printf '%-50s %s\n' "-----" "------"
for i in "${!NAMES[@]}"; do
    printf '%-50s %s\n' "${NAMES[$i]}" "${RESULTS[$i]}"
done

if [ "$overall" -eq 0 ]; then
    printf '\nHealth snapshot: ALL CHECKS PASSED\n'
else
    printf '\nHealth snapshot: FAILURES DETECTED (details on stderr above)\n'
fi
exit "$overall"
