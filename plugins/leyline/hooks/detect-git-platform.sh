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
# Performance: <50ms typical

set -euo pipefail

# --- Detection Logic ---

detect_platform() {
    local platform="unknown"
    local cli_tool=""
    local mr_term="pull request"
    local ci_system=""

    # Signal 1: Git remote URL (highest confidence)
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local remote_url
        remote_url=$(git remote get-url origin 2>/dev/null || echo "")

        case "$remote_url" in
            *github.com*|*github.*)
                platform="github"
                cli_tool="gh"
                mr_term="pull request"
                ;;
            *gitlab.com*|*gitlab.*)
                platform="gitlab"
                cli_tool="glab"
                mr_term="merge request"
                ;;
            *bitbucket.org*|*bitbucket.*)
                platform="bitbucket"
                cli_tool=""
                mr_term="pull request"
                ;;
        esac
    fi

    # Signal 2: File/directory markers (fallback if remote didn't match)
    if [ "$platform" = "unknown" ]; then
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
    fi

    # Signal 3: CLI availability (confirms tool exists, or discovers platform inside git repos only)
    if [ -n "$cli_tool" ]; then
        if ! command -v "$cli_tool" >/dev/null 2>&1; then
            cli_tool="${cli_tool} (not installed)"
        fi
    elif [ "$platform" = "unknown" ] && git rev-parse --git-dir > /dev/null 2>&1; then
        # Last resort (git repos only): infer platform from installed CLI
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

    # Detect CI config
    if [ -d ".github/workflows" ]; then
        ci_system="github-actions"
    elif [ -f ".gitlab-ci.yml" ]; then
        ci_system="gitlab-ci"
    elif [ -f "bitbucket-pipelines.yml" ]; then
        ci_system="bitbucket-pipelines"
    fi

    printf '%s|%s|%s|%s' "$platform" "$cli_tool" "$mr_term" "$ci_system"
}

# --- Main ---

result=$(detect_platform)
IFS='|' read -r platform cli_tool mr_term ci_system <<< "$result"

# Skip injection if we couldn't detect anything
if [ "$platform" = "unknown" ]; then
    cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": ""
  }
}
EOF
    exit 0
fi

# Build context message
context="git_platform: ${platform}, cli: ${cli_tool}, mr_term: ${mr_term}"
if [ -n "$ci_system" ]; then
    context="${context}, ci: ${ci_system}"
fi

# Add platform-specific guidance
case "$platform" in
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

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${context}"
  }
}
EOF

exit 0
