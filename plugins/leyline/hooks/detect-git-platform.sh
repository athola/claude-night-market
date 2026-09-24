#!/usr/bin/env bash
# SessionStart hook for leyline - Git platform detection
# Detects whether the current project uses GitHub, GitLab, or Bitbucket
# and injects platform context into every session.
#
# Detection priority:
#   1. Git remote URL (most reliable)
#   2. Directory/file markers (.github/, .gitlab-ci.yml, etc.)
#   3. CLI tool availability (gh, glab)
#
# Output: Injects git_platform, cli_tool, and mr_term into session context
#
# Performance: dominated by process start-up, not by work. On a loaded
# macOS laptop one `git` invocation measured 0.53s wall, so the budget is
# spent in whole processes: this hook runs one `git` and no interpreter.
# Measured 0.8-1.1s idle against the 2s its hooks.json entry declares.

set -euo pipefail

# --- Detection Logic ---

detect_platform() {
  local platform="unknown"
  local cli_tool=""
  local mr_term="pull request"
  local ci_system=""

  # Signal 1: Git remote URL (highest confidence).
  # `git remote get-url` fails outside a work tree as well as inside
  # one with no origin, and an empty result matches no arm below, so
  # the separate `git rev-parse` that used to gate this is redundant
  # here. It survives at signal 3, where repo-ness is what is actually
  # being asked, and only on the path that reaches it. A git
  # invocation costs ~0.5s of process start-up on a loaded macOS
  # laptop, which is half this hook's budget.
  local remote_url
  remote_url=$(git remote get-url origin 2>/dev/null || :)

  case "${remote_url}" in
    *github.com* | *github.*)
      platform="github"
      cli_tool="gh"
      mr_term="pull request"
      ;;
    *gitlab.com* | *gitlab.*)
      platform="gitlab"
      cli_tool="glab"
      mr_term="merge request"
      ;;
    *bitbucket.org* | *bitbucket.*)
      platform="bitbucket"
      cli_tool=""
      mr_term="pull request"
      ;;
  esac

  # Signal 2: File/directory markers (fallback if remote didn't match)
  case "${platform}" in
    unknown)
      if [ -d ".github" ]; then
        platform="github"
        cli_tool="gh"
        mr_term="pull request"
      elif [ -f ".gitlab-ci.yml" ]; then
        platform="gitlab"
        cli_tool="glab"
        mr_term="merge request"
      elif [ -f "bitbucket-pipelines.yml" ]; then
        platform="bitbucket"
        cli_tool=""
        mr_term="pull request"
      fi
      ;;
  esac

  # Signal 3: CLI availability (confirms tool exists, or discovers platform inside git repos only)
  case "${cli_tool}:${platform}" in
    :unknown)
      # Last resort (git repos only): infer platform from installed CLI
      if git rev-parse --git-dir >/dev/null 2>&1; then
        if command -v gh >/dev/null 2>&1; then
          platform="github"
          cli_tool="gh"
          mr_term="pull request"
        elif command -v glab >/dev/null 2>&1; then
          platform="gitlab"
          cli_tool="glab"
          mr_term="merge request"
        fi
      fi
      ;;
    :*) ;;
    *)
      if ! command -v "${cli_tool}" >/dev/null 2>&1; then
        cli_tool="${cli_tool} (not installed)"
      fi
      ;;
  esac

  # Detect CI config
  if [ -d ".github/workflows" ]; then
    ci_system="github-actions"
  elif [ -f ".gitlab-ci.yml" ]; then
    ci_system="gitlab-ci"
  elif [ -f "bitbucket-pipelines.yml" ]; then
    ci_system="bitbucket-pipelines"
  fi

  printf '%s|%s|%s|%s' "${platform}" "${cli_tool}" "${mr_term}" "${ci_system}"
}

# --- Main ---

main() {
  # Claude Code passes no argv; -x/-t exists for debugging by hand.
  case "${1:-}" in
    -x | -t) set -x ;;
  esac

  local result platform cli_tool mr_term ci_system context
  result=$(detect_platform)
  IFS='|' read -r platform cli_tool mr_term ci_system <<<"${result}"

  # Skip injection if we couldn't detect anything
  case "${platform}" in
    unknown)
      cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
      exit 0
      ;;
  esac

  # Build context message
  context="git_platform: ${platform}, cli: ${cli_tool}, mr_term: ${mr_term}"
  case "${ci_system}" in
    "") ;;
    *) context="${context}, ci: ${ci_system}" ;;
  esac

  # Add platform-specific guidance
  case "${platform}" in
    github)
      context="${context}. Use \`gh\` CLI for issues, PRs, and API calls. Refer to Skill(leyline:git-platform) for command reference."
      ;;
    gitlab)
      context="${context}. Use \`glab\` CLI for issues, MRs, and API calls. Use 'merge request' instead of 'pull request'. Refer to Skill(leyline:git-platform) for command mapping."
      ;;
    bitbucket)
      context="${context}. Bitbucket has limited CLI support. Use REST API or web interface for issues and PRs. Refer to Skill(leyline:git-platform) for alternatives."
      ;;
  esac

  # Context is assembled from this script's own literals: `platform`,
  # `cli_tool`, `mr_term` and `ci_system` each come from a fixed `case`
  # arm, so there is nothing here for jq to escape that the heredoc cannot
  # emit. The jq branch this replaced cost a process on every session for
  # a string the script already controlled, and left two output paths to
  # keep in agreement.
  cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${context}"
  }
}
EOF

  exit 0
}

main "$@"
