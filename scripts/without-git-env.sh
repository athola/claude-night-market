#!/usr/bin/env bash
# Run a command with every GIT_* variable removed from its environment.
#
# Usage:
#   ./scripts/without-git-env.sh [-h] [-x|-t] <command> [args...]
#
# Why this exists. git exports its context to every hook it runs. Commit from
# a linked worktree and the hook's children inherit GIT_DIR and GIT_INDEX_FILE
# pointing at the *outer* repository; a test suite that shells out to git in a
# temp directory then writes to that index instead of its own. Issue #609 is
# what that looks like from the outside: ~2,800 phantom staged deletions in a
# worktree nobody had touched.
#
# Why the whole prefix, and not a list of names. The fix this replaces unset
# three variables by name. A commit from a linked worktree exports eight, so
# six went on through, and the next variable git adds would have too. The
# category is the invariant worth enforcing, so the category is what gets
# scrubbed: no GIT_* variable reaches a test, whatever it is called.
#
# Callers: scripts/run-plugin-tests.sh, the `test-ecosystem` Makefile target.
# Guarded by tests/unit/test_run_plugin_tests.py::TestGitEnvScrub, which
# asserts both that no GIT_* survives and that every invocation goes through
# here.

set -euo pipefail

# A bare name (`bash without-git-env.sh` from inside scripts/) has no slash
# for `${0%/*}` to strip, so it would come back unchanged.
case "${0}" in
  */*) MYDIR="${0%/*}" ;;
  *) MYDIR="." ;;
esac
readonly MYDIR

# shellcheck source=scripts/logging.sh
. "${MYDIR%/}/logging.sh"

readonly EX_USAGE=64

usage() {
  log "Usage: scripts/without-git-env.sh [-h] [-x|-t] <command> [args...]"
  printf '  -h          Show this help and exit (exit 0)\n'
  printf '  -x, -t      Enable xtrace (set -x) for debugging\n'
  printf '  <command>   Run with every GIT_* variable unset; its exit status is ours\n'
}

main() {
  # Only exact flags before the command are ours. Everything from the first
  # other word on is the command, so a program whose name ends in "help"
  # still runs instead of printing this script's usage.
  while [ "${#}" -gt 0 ]; do
    case "${1}" in
      -h | --help)
        usage
        exit 0
        ;;
      -x | -t)
        set -x
        shift
        ;;
      *) break ;;
    esac
  done

  case "${#}" in
    0)
      usage >&2
      exit "${EX_USAGE}"
      ;;
  esac

  # "${!GIT_@}" expands to the names of the set variables starting with GIT_.
  # With none set it expands to zero words, which is why the loop body is safe
  # under `set -u` outside a git hook.
  local git_var
  for git_var in "${!GIT_@}"; do
    unset "${git_var}"
  done

  # exec, so the child's exit status is this script's exit status and a
  # failing suite still fails the gate.
  exec "$@"
}

main "$@"
