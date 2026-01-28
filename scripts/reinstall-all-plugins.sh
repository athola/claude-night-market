#!/usr/bin/env bash
set -euo pipefail

#
# Reinstall Claude Code plugins generically (no hardcoded plugin list).
#
# Default behavior:
# - Reads installed plugins from ~/.claude/plugins/installed_plugins.json
# - For each selected plugin:
#     1) Uninstall via `claude plugin uninstall`
#     2) Reinstall via `claude plugin install`
#
# This is intentionally conservative: it never assumes a particular marketplace or plugin set.
#

usage() {
  cat <<'USAGE'
Usage:
  scripts/reinstall-all-plugins.sh [options]

Options:
  --only REGEX            Only reinstall plugins whose id matches REGEX (e.g. '^pensive@')
  --dry-run               Print actions without modifying anything
  --list                  Print plugins + resolved paths, then exit
  --installed-json PATH   Override installed_plugins.json (default: ~/.claude/plugins/installed_plugins.json)
  --scope SCOPE           Claude plugin scope: user, project, or local (default: user)
  --help                  Show this help

Notes:
  - Plugin ids are interpreted as "<plugin>@<marketplace>".
  - This uses Claude Code's plugin manager (`claude plugin ...`) so it works with any marketplace/source.
  - `--list` prints only what your Claude install thinks is installed (from installed_plugins.json).
USAGE
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "error: missing required command: $cmd" >&2
    exit 2
  fi
}

emit() { printf "%s\n" "$*" 2>/dev/null || exit 0; }
log() { emit "$*"; }
warn() { printf "warning: %s\n" "$*" >&2 || true; }
die() { printf "error: %s\n" "$*" >&2 || true; exit 2; }

require_cmd jq
require_cmd claude
require_cmd rg

only_regex=""
dry_run=0
list_only=0
installed_json="${HOME}/.claude/plugins/installed_plugins.json"
scope="user"

while [ $# -gt 0 ]; do
  case "$1" in
    --only)
      only_regex="${2:-}"; shift 2 ;;
    --dry-run)
      dry_run=1; shift ;;
    --list)
      list_only=1; shift ;;
    --installed-json)
      installed_json="${2:-}"; shift 2 ;;
    --scope)
      scope="${2:-}"; shift 2 ;;
    --help|-h)
      usage; exit 0 ;;
    *)
      die "unknown argument: $1" ;;
  esac
done

[ -f "$installed_json" ] || die "installed plugins file not found: $installed_json"

tmp_dir="$(mktemp -d)"
cleanup() { rm -rf "$tmp_dir"; }
trap cleanup EXIT

plugin_ids_file="${tmp_dir}/plugin_ids.txt"
failures_file="${tmp_dir}/failures.txt"
: >"$failures_file"

# installed_plugins.json (v2) structure:
# { version: 2, plugins: { "<plugin>@<marketplace>": [ { installPath, version, ... }, ... ] , ... } }
jq -r '.plugins | keys[]' "$installed_json" | sort >"$plugin_ids_file"

list_plugins() {
  while IFS= read -r plugin_id; do
    if [ -n "$only_regex" ] && ! printf "%s" "$plugin_id" | rg -q "$only_regex"; then
      continue
    fi
    local install_path version
    install_path="$(jq -r --arg id "$plugin_id" '.plugins[$id][0].installPath // empty' "$installed_json")"
    version="$(jq -r --arg id "$plugin_id" '.plugins[$id][0].version // empty' "$installed_json")"

    log "id=$plugin_id"
    log "  installPath=$install_path"
    log "  version=$version"
  done <"$plugin_ids_file"
}

if [ "$list_only" -eq 1 ]; then
  list_plugins
  exit 0
fi

errors=0
max_retries=3
retry_delay=2

retry_cmd() {
  local attempt
  for attempt in $(seq 1 "$max_retries"); do
    if "$@" 2>&1; then
      return 0
    fi
    if [ "$attempt" -lt "$max_retries" ]; then
      warn "attempt $attempt/$max_retries failed, retrying in ${retry_delay}s..."
      sleep "$retry_delay"
    fi
  done
  return 1
}

while IFS= read -r plugin_id; do
  if [ -n "$only_regex" ] && ! printf "%s" "$plugin_id" | rg -q "$only_regex"; then
    continue
  fi

  log "== Reinstall: $plugin_id =="

  if [ "$dry_run" -eq 1 ]; then
    log "  would run: claude plugin uninstall --scope $scope $plugin_id"
    log "  would run: claude plugin install --scope $scope $plugin_id"
    continue
  fi

  # Uninstall first (ignore failures so we still attempt install).
  if ! retry_cmd claude plugin uninstall --scope "$scope" "$plugin_id"; then
    warn "uninstall failed for $plugin_id (scope=$scope); continuing to install"
  fi

  if ! retry_cmd claude plugin install --scope "$scope" "$plugin_id"; then
    warn "install failed for $plugin_id (scope=$scope)"
    errors=$((errors + 1))
    printf "%s\n" "$plugin_id install failed" >>"$failures_file"
  fi

  # Small delay between plugins to avoid rate limiting.
  sleep 1

done <"$plugin_ids_file"

if [ "$errors" -ne 0 ]; then
  warn "completed with $errors issue(s). See failures:"
  sed 's/^/  /' "$failures_file" >&2 || true
  exit 1
fi

log "done"
