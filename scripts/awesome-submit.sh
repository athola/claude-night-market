#!/usr/bin/env bash
# Submit night-market to awesome-openclaw lists via fork PRs.
# Uses your existing `gh auth` session. No PAT or secrets needed.
#
# Usage:
#   ./scripts/awesome-submit.sh v1.8.1 --dry-run
#   ./scripts/awesome-submit.sh v1.8.1 --issue vincentkoc/awesome-openclaw#123

set -euo pipefail

# A bare name (`bash awesome-submit.sh` from inside scripts/) has no slash
# for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

REPO_ROOT="$(cd "${MYDIR%/}/.." && pwd)"
readonly REPO_ROOT
readonly REQUIRED_DEPENDENCIES="gh git python3"

# Each target: repo|README section the entry goes under|submission flow.
# "issue-first" lists close PRs that arrive without an approved issue.
# SamurAIGPT/awesome-openclaw is gone: it was transferred and renamed to a
# Meta Muse connector catalog, and following the redirect opened an
# off-topic PR there (closed). Re-check a list's CONTRIBUTING.md before
# adding it here.
readonly TARGETS=(
  "vincentkoc/awesome-openclaw|## Skills and Skill Indexes|issue-first"
)

DRY_RUN=false
VERSION=""
# Space-separated owner/repo#N, one per approved resource-request issue.
APPROVED_ISSUES=""
XTRACE=0
FORK_OWNER=""
SKILLS=""
ENTRY=""
# Set per target inside submit_target's subshell, never in this shell.
WORKDIR=""

usage() {
  log "Usage: scripts/awesome-submit.sh [-h] [-x|-t] [--dry-run] [VERSION]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  --dry-run   Commit in a clone of each upstream; fork, push and open no PR\n'
  printf '  --issue R   Approved issue for a list, as owner/repo#N (repeatable)\n'
  printf '  VERSION     Release version, v1.8.1 or 1.8.1 (default: abstract plugin.json)\n'
}

depcheck() {
  local missing="" utility
  for utility in ${REQUIRED_DEPENDENCIES}; do
    command -v "${utility}" >/dev/null 2>&1 ||
      missing="${missing:+"${missing} "}${utility}"
  done
  case "${missing}" in
    "") return 0 ;;
  esac
  log 5 "Required utilities not found: ${missing}"
  log 5 "gh installs from https://cli.github.com"
  return 1
}

parse_args() {
  local arg
  while [ "$#" -gt 0 ]; do
    arg="${1}"
    shift
    case "${arg}" in
      *[uU][sS][aA][gG][eE] | *[hH][eE][lL][pP] | -h)
        usage
        exit 0
        ;;
      -x | -t) XTRACE=1 ;;
      --dry-run) DRY_RUN=true ;;
      --issue)
        case "${1:-}" in
          */*#[0-9]*) APPROVED_ISSUES="${APPROVED_ISSUES:+"${APPROVED_ISSUES} "}${1}" ;;
          *)
            log 4 "--issue needs owner/repo#N, got: ${1:-nothing}"
            exit 1
            ;;
        esac
        shift
        ;;
      v*) VERSION="${arg}" ;;
      [0-9]*) VERSION="v${arg}" ;;
      *)
        log 4 "Unknown argument: ${arg}"
        exit 1
        ;;
    esac
  done
}

# Print the approved issue recorded for a target, or nothing.
approved_issue() {
  local target="${1:?approved_issue needs a target}" issue
  for issue in ${APPROVED_ISSUES}; do
    case "${issue}" in
      "${target}#"*) printf '%s\n' "${issue}" ;;
    esac
  done
}

# `env` sets the variables the Python programs read, because the shell
# refuses a prefix assignment to a readonly variable.

detect_version() {
  case "${VERSION}" in
    "") ;;
    *) return 0 ;;
  esac
  VERSION="v$(env REPO_ROOT="${REPO_ROOT}" python3 -c '
import json, os
print(json.load(open(os.path.join(os.environ["REPO_ROOT"], "plugins/abstract/.claude-plugin/plugin.json")))["version"])
')"
  log "Auto-detected version: ${VERSION}"
}

# Count skills from export manifest or plugin.json
count_skills() {
  if [ -f "${REPO_ROOT}/clawhub/manifest.json" ]; then
    env REPO_ROOT="${REPO_ROOT}" python3 -c '
import json, os
print(json.load(open(os.path.join(os.environ["REPO_ROOT"], "clawhub/manifest.json")))["total_exported"])
'
  else
    printf '%s\n' "100+"
  fi
}

# Runs in a subshell per target: the cd into the clone and the cleanup
# trap end with it, and set -e still aborts the whole run on a failure.
submit_target() {
  local spec="${1:?submit_target needs a target}"
  local target section flow issue resolved
  local base_owner repo_name branch fork_name existing existing_num existing_url
  local clone_source lease existing_pr

  target="${spec%%|*}"
  section="${spec#*|}"
  flow="${section#*|}"
  section="${section%%|*}"

  log "=== ${target} ==="

  # A transferred or renamed repo answers under its new name, and it is a
  # different list with its own scope.
  resolved=$(gh api "repos/${target}" --jq .full_name 2>/dev/null || true)
  case "${resolved}" in
    "${target}") ;;
    *)
      log 3 "${target} now resolves to ${resolved:-nothing}; skipping. Read its CONTRIBUTING.md before adding it back."
      return 0
      ;;
  esac

  issue=$(approved_issue "${target}")
  case "${flow}:${issue}:${DRY_RUN}" in
    issue-first::false)
      log "${target} takes no PR without an approved issue."
      log "Open an 'Add Resource Request' issue there first, disclose that you maintain night-market, and name the section '${section}'."
      log "Once a maintainer approves it, rerun with: --issue ${target}#<number>"
      return 0
      ;;
  esac

  base_owner="${target%%/*}"
  repo_name="${target#*/}"
  repo_name="${repo_name%%/*}"
  branch="add-night-market-${VERSION}"

  # Issue #571: TARGETS contains two repos with the SAME name
  # (vincentkoc/awesome-openclaw and SamurAIGPT/awesome-openclaw).
  # A single account can only hold one fork named "awesome-openclaw",
  # so reusing it sends a PR against the wrong upstream and GitHub
  # rejects it ("No commits between SamurAIGPT:main and athola:...").
  # Give each upstream its own fork, named after the upstream owner,
  # so every PR is created from a fork whose parent matches its target.
  fork_name="${repo_name}-${base_owner}"

  # Check for existing open PR from us before doing any work
  existing=$(gh pr list \
    --repo "${target}" \
    --author "${FORK_OWNER}" \
    --search "night-market" \
    --state open \
    --json number,url -q '.[0]' 2>/dev/null || true)

  case "${existing}" in
    "" | null) ;;
    *)
      existing_num=$(printf '%s\n' "${existing}" | python3 -c "import sys,json; print(json.load(sys.stdin)['number'])")
      existing_url=$(printf '%s\n' "${existing}" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
      log "Open PR #${existing_num} already exists: ${existing_url}"
      log "Skipping ${target}"
      return 0
      ;;
  esac

  # A dry run previews against the upstream itself. Forking and syncing
  # are changes on GitHub, and they ran before the dry-run check below.
  clone_source="${target}"
  case "${DRY_RUN}" in
    true) ;;
    *)
      # Ensure a dedicated fork exists for THIS upstream.
      gh repo fork "${target}" --fork-name "${fork_name}" --clone=false 2>&1 || true

      if ! gh repo view "${FORK_OWNER}/${fork_name}" --json name -q .name >/dev/null 2>&1; then
        log 2 "Cannot access fork ${FORK_OWNER}/${fork_name}, skipping"
        return 0
      fi

      # A fork that did not sync would carry the PR against an old main.
      if ! gh repo sync "${FORK_OWNER}/${fork_name}" --branch main 2>&1; then
        log 2 "fork sync failed for ${FORK_OWNER}/${fork_name}; skipping ${target}"
        return 0
      fi
      clone_source="${FORK_OWNER}/${fork_name}"
      ;;
  esac

  # Global, not local: the EXIT trap runs after this function has returned.
  WORKDIR=$(mktemp -d)
  trap 'rm -rf "${WORKDIR}"' EXIT INT TERM

  gh repo clone "${clone_source}" "${WORKDIR}/repo" -- --depth=10
  cd "${WORKDIR}/repo"

  git config user.name "${FORK_OWNER}"
  git config user.email "${FORK_OWNER}@users.noreply.github.com"

  git checkout -b "${branch}"

  # Add entry if not already present in upstream
  if grep -q "night-market" README.md; then
    log "Already listed in ${target}, skipping"
    return 0
  fi

  # The entry goes at the end of the target's own section. A list without
  # that heading is refused: appending at end of file put the line after
  # the README footer, in no list at all.
  if ! env ENTRY_LINE="${ENTRY}" SECTION="${section}" python3 <<'PYEOF'; then
import os, sys
entry, section = os.environ["ENTRY_LINE"], os.environ["SECTION"]
lines = open("README.md").read().split("\n")
if section not in lines:
    sys.exit(1)
start = lines.index(section) + 1
end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
last = max((i for i in range(start, end) if lines[i].startswith("- ")), default=start)
lines.insert(last + 1, entry)
open("README.md", "w").write("\n".join(lines))
PYEOF
    log 3 "${target} has no '${section}' section; skipping. Check where its CONTRIBUTING.md wants skills listed."
    return 0
  fi

  if git diff --quiet; then
    log "No changes needed"
    return 0
  fi

  git add README.md
  git commit -m "Add night-market: ${SKILLS} skills for code review, testing, architecture"

  log "Changes:"
  git diff HEAD~1 --stat

  case "${DRY_RUN}" in
    true)
      log "Dry run -- skipping push/PR for ${target}"
      return 0
      ;;
  esac

  # The shallow clone is single-branch, so a branch left by an earlier run
  # is neither fetched nor treated as tracked, and a bare --force-with-lease
  # rejected the push as stale. Fetch it and name the expected value; an
  # empty value means the branch must not exist yet.
  git fetch -q --depth=1 origin "+refs/heads/${branch}:refs/remotes/origin/${branch}" 2>/dev/null || true
  lease=$(git rev-parse -q --verify "refs/remotes/origin/${branch}" || true)
  git push --force-with-lease="${branch}:${lease}" origin "${branch}"

  # Check if a PR already exists for this branch (e.g. from a prior failed run)
  existing_pr=$(gh pr list \
    --repo "${target}" \
    --head "${FORK_OWNER}:${branch}" \
    --state open \
    --json number -q '.[0].number' 2>/dev/null || true)

  case "${existing_pr}" in
    "") ;;
    *)
      log "PR #${existing_pr} updated on ${target}"
      return 0
      ;;
  esac

  gh pr create \
    --repo "${target}" \
    --head "${FORK_OWNER}:${branch}" \
    --title "Add night-market skills" \
    --body "Adds [Claude Night Market](https://github.com/athola/claude-night-market) under ${section}: curated skills for code review, testing, documentation, architecture, and git workflows. MIT licensed, published on ClawHub.

Approved in ${issue:-no issue}. I maintain night-market."
  log "PR created on ${target}"
}

main() {
  local target

  parse_args "$@"

  case "${XTRACE}" in
    1) set -x ;;
  esac

  depcheck || exit 1
  detect_version

  if ! gh auth status >/dev/null 2>&1; then
    log 4 "Not authenticated. Run: gh auth login"
    exit 1
  fi

  FORK_OWNER=$(gh api user --jq .login)
  log "Authenticated as: ${FORK_OWNER}"

  SKILLS=$(count_skills)
  ENTRY="- [night-market](https://github.com/athola/claude-night-market) - ${SKILLS} curated skills for code review, testing, docs, and architecture."

  for target in "${TARGETS[@]}"; do
    (submit_target "${target}")
  done

  log "=== Done ==="
}

main "$@"
