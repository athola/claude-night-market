#!/usr/bin/env bash
#
# Interactive Authentication Module
# Provides token caching, session management, and multi-service support
#
# Usage:
#   source plugins/leyline/skills/authentication-patterns/modules/interactive-auth.sh
#   ensure_auth github || exit 1
#

# ============================================================================
# CONFIGURATION
# ============================================================================

AUTH_CACHE_DIR="${AUTH_CACHE_DIR:-$HOME/.cache/claude-auth}"
AUTH_CACHE_TTL="${AUTH_CACHE_TTL:-300}"  # 5 minutes
AUTH_SESSION_TTL="${AUTH_SESSION_TTL:-86400}"  # 24 hours
AUTH_INTERACTIVE="${AUTH_INTERACTIVE:-auto}"
AUTH_MAX_ATTEMPTS="${AUTH_MAX_ATTEMPTS:-3}"

# Service-specific auth commands
declare -A AUTH_CHECK_COMMANDS=(
  [github]="gh auth status"
  [gitlab]="glab auth status"
  [aws]="aws sts get-caller-identity"
  [gcloud]="gcloud auth list --filter=account:* --format=csv"
  [azure]="az account show"
)

# Service-specific login commands
declare -A AUTH_LOGIN_COMMANDS=(
  [github]="gh auth login"
  [gitlab]="glab auth login"
  [aws]="aws configure"
  [gcloud]="gcloud auth login"
  [azure]="az login"
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Get current timestamp in seconds
get_timestamp() {
  date +%s
}

# Check if running in interactive mode
is_interactive() {
  case "$AUTH_INTERACTIVE" in
    true|1|yes) return 0 ;;
    false|0|no) return 1 ;;
    auto)
      [[ -t 0 ]] && return 0 || return 1
      ;;
    *) return 1 ;;
  esac
}

# Check if running in CI/CD
is_ci() {
  [[ -n "$CI" ]] || [[ -n "$GITHUB_ACTIONS" ]] || \
  [[ -n "$GITLAB_CI" ]] || [[ -n "$AWS_EXECUTION_ENV" ]]
}

# Initialize cache directory
init_cache_dir() {
  local service="$1"
  local cache_path="$AUTH_CACHE_DIR/$service"

  if [[ ! -d "$cache_path" ]]; then
    mkdir -p "$cache_path"
    chmod 0700 "$cache_path"
  fi
}

# Read JSON value from file
read_json_value() {
  local file="$1"
  local key="$2"

  if command -v jq &>/dev/null; then
    jq -r ".$key // empty" "$file" 2>/dev/null
  else
    # Fallback: simple grep for JSON
    grep -o "\"$key\"\s*:\s*\"[^\"]*\"" "$file" 2>/dev/null | \
      sed 's/.*: *"\([^"]*\)".*/\1/'
  fi
}

# Write JSON key-value to file
write_json_value() {
  local file="$1"
  local key="$2"
  local value="$3"

  if command -v jq &>/dev/null; then
    if [[ -f "$file" ]]; then
      tmpfile=$(mktemp)
      jq ".$key = \"$value\"" "$file" > "$tmpfile" && mv "$tmpfile" "$file"
    else
      echo "{\"$key\": \"$value\"}" > "$file"
    fi
  else
    # Fallback: simple JSON write
    echo "{\"$key\": \"$value\"}" > "$file"
  fi
}

# ============================================================================
# CACHE FUNCTIONS
# ============================================================================

# Check if cache entry is valid
check_cache() {
  local service="$1"
  local cache_file="$AUTH_CACHE_DIR/$service/auth_status.json"

  if [[ ! -f "$cache_file" ]]; then
    return 1
  fi

  local last_verified=$(read_json_value "$cache_file" "last_verified")
  local current_time=$(get_timestamp)

  if [[ -z "$last_verified" ]]; then
    return 1
  fi

  local cache_age=$((current_time - last_verified))

  if [[ $cache_age -lt $AUTH_CACHE_TTL ]]; then
    return 0  # Cache is valid
  else
    return 1  # Cache expired
  fi
}

# Write cache entry
write_cache() {
  local service="$1"
  local authenticated="$2"
  local cache_file="$AUTH_CACHE_DIR/$service/auth_status.json"

  init_cache_dir "$service"

  local current_time=$(get_timestamp)

  cat > "$cache_file" << EOF
{
  "authenticated": $authenticated,
  "last_verified": $current_time,
  "cache_ttl": $AUTH_CACHE_TTL,
  "service": "$service"
}
EOF
}

# Invalidate cache for a service
invalidate_auth_cache() {
  local service="$1"
  local cache_file="$AUTH_CACHE_DIR/$service/auth_status.json"

  if [[ -f "$cache_file" ]]; then
    rm -f "$cache_file"
    echo "✓ Cache invalidated for $service"
  fi
}

# Clear all auth caches
clear_all_auth_cache() {
  if [[ -d "$AUTH_CACHE_DIR" ]]; then
    rm -rf "$AUTH_CACHE_DIR"
    echo "✓ All authentication caches cleared"
  fi
}

# ============================================================================
# SESSION FUNCTIONS
# ============================================================================

# Load session for a service
load_session() {
  local service="$1"
  local session_file="$AUTH_CACHE_DIR/$service/session.json"

  if [[ ! -f "$session_file" ]]; then
    return 1
  fi

  local session_created=$(read_json_value "$session_file" "created_at")
  local current_time=$(get_timestamp)

  if [[ -z "$session_created" ]]; then
    return 1
  fi

  local session_age=$((current_time - session_created))

  if [[ $session_age -lt $AUTH_SESSION_TTL ]]; then
    return 0  # Session is valid
  else
    return 1  # Session expired
  fi
}

# Create session for a service
create_session() {
  local service="$1"
  local session_file="$AUTH_CACHE_DIR/$service/session.json"

  init_cache_dir "$service"

  local current_time=$(get_timestamp)

  cat > "$session_file" << EOF
{
  "service": "$service",
  "created_at": $current_time,
  "session_ttl": $AUTH_SESSION_TTL,
  "hostname": "$(hostname)",
  "user": "$(whoami)"
}
EOF

  chmod 0600 "$session_file"
}

# ============================================================================
# AUTHENTICATION CHECKS
# ============================================================================

# Check if service is authenticated (non-interactive)
check_auth_status() {
  local service="$1"
  local check_cmd="${AUTH_CHECK_COMMANDS[$service]}"

  if [[ -z "$check_cmd" ]]; then
    echo "❌ Unknown service: $service" >&2
    return 1
  fi

  # Check command availability
  local cmd_name="${check_cmd%% *}"
  if ! command -v "$cmd_name" &>/dev/null; then
    echo "❌ $cmd_name not found" >&2
    return 1
  fi

  # Run check command
  eval "$check_cmd" &>/dev/null
  return $?
}

# ============================================================================
# AUTHENTICATION PROMPTS
# ============================================================================

# Prompt for GitHub authentication
prompt_github_auth() {
  cat << 'EOF'

🔐 GitHub Authentication Required

This workflow needs GitHub API access to continue.

How would you like to authenticate?
  1. Browser (OAuth) - Recommended
  2. Personal Access Token
  3. Cancel workflow

Choose [1-3]:
EOF

  read -r choice

  case "$choice" in
    1)
      echo "Opening browser for OAuth authentication..."
      echo "Follow the prompts in your browser."

      if gh auth login; then
        echo "✓ OAuth authentication successful"
        return 0
      else
        echo "❌ OAuth authentication failed"
        return 1
      fi
      ;;
    2)
      echo ""
      echo "Enter your GitHub personal access token:"
      echo "(Token will not be echoed)"
      read -rs token
      echo ""

      if echo "$token" | gh auth login --with-token; then
        echo "✓ Token authentication successful"
        return 0
      else
        echo "❌ Token authentication failed"
        return 1
      fi
      ;;
    3)
      echo "Workflow cancelled."
      return 1
      ;;
    *)
      echo "❌ Invalid choice"
      return 1
      ;;
  esac
}

# Prompt for generic service authentication
prompt_service_auth() {
  local service="$1"
  local login_cmd="${AUTH_LOGIN_COMMANDS[$service]}"

  cat << EOF

🔐 $service Authentication Required

This workflow needs $service API access to continue.

Running: $login_cmd

EOF

  if eval "$login_cmd"; then
    echo "✓ $service authentication successful"
    return 0
  else
    echo "❌ $service authentication failed"
    return 1
  fi
}

# ============================================================================
# MAIN ENSURE AUTH FUNCTION
# ============================================================================

# Ensure authentication for a service
ensure_auth() {
  local service="$1"
  local attempt=0

  if [[ -z "$service" ]]; then
    echo "❌ Usage: ensure_auth <service>" >&2
    return 1
  fi

  # Check if service is supported
  if [[ -z "${AUTH_CHECK_COMMANDS[$service]}" ]]; then
    echo "❌ Unsupported service: $service" >&2
    echo "Supported services: ${!AUTH_CHECK_COMMANDS[@]}" >&2
    return 1
  fi

  # Retry loop with exponential backoff
  while [[ $attempt -lt $AUTH_MAX_ATTEMPTS ]]; do
    # Check cache first (fast path)
    if check_cache "$service"; then
      return 0
    fi

    # Check session (medium path)
    if load_session "$service"; then
      # Session valid, verify auth status
      if check_auth_status "$service"; then
        write_cache "$service" "true"
        return 0
      fi
    fi

    # Full authentication check (slow path)
    if check_auth_status "$service"; then
      create_session "$service"
      write_cache "$service" "true"
      return 0
    fi

    # Authentication failed - attempt to authenticate
    attempt=$((attempt + 1))

    if [[ $attempt -ge $AUTH_MAX_ATTEMPTS ]]; then
      echo "❌ Maximum authentication attempts ($AUTH_MAX_ATTEMPTS) reached for $service" >&2
      return 1
    fi

    # Check if we should prompt
    if is_ci; then
      # CI/CD: Use environment variables
      if [[ "$service" == "github" ]] && [[ -n "$GITHUB_TOKEN" ]]; then
        echo "🔐 Using GITHUB_TOKEN from environment"
        echo "$GITHUB_TOKEN" | gh auth login --with-token &>/dev/null
        continue
      elif [[ "$service" == "gitlab" ]] && [[ -n "$GITLAB_TOKEN" ]]; then
        echo "🔐 Using GITLAB_TOKEN from environment"
        # GitLab token handling depends on version
        continue
      else
        echo "❌ $service authentication required in CI/CD" >&2
        echo "Set the appropriate environment variable (e.g., GITHUB_TOKEN)" >&2
        return 1
      fi
    fi

    if ! is_interactive; then
      echo "❌ $service authentication required but non-interactive mode" >&2
      return 1
    fi

    # Prompt user for authentication
    echo "🔐 $service authentication required (attempt $attempt/$AUTH_MAX_ATTEMPTS)"

    if [[ "$service" == "github" ]]; then
      prompt_github_auth || continue
    else
      prompt_service_auth "$service" || continue
    fi

    # If we get here, auth succeeded, loop will verify and return
  done

  return 1
}

# ============================================================================
# WRAPPER FUNCTIONS
# ============================================================================

# Wrapper for gh commands with automatic auth
gh_with_auth() {
  ensure_auth github || return 1
  gh "$@"
}

# Wrapper for gh api calls
gh_api_with_auth() {
  ensure_auth github || return 1
  gh api "$@"
}

# Wrapper for gitlab commands
glab_with_auth() {
  ensure_auth gitlab || return 1
  glab "$@"
}

# Wrapper for aws commands
aws_with_auth() {
  ensure_auth aws || return 1
  aws "$@"
}

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

# Export main functions
export -f ensure_auth
export -f check_auth_status
export -f invalidate_auth_cache
export -f clear_all_auth_cache
export -f is_interactive
export -f is_ci

# Export wrapper functions
export -f gh_with_auth
export -f gh_api_with_auth
export -f glab_with_auth
export -f aws_with_auth
