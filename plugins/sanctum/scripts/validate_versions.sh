#!/bin/bash
# Version validation script for claude-night-market
# Used by /pr-review Phase 1.5 to check version consistency
#
# Usage: validate_versions.sh [PR_NUMBER]
#   If PR_NUMBER provided, checks only files changed in that PR
#   Otherwise, validates entire repository

set -e

PR_NUMBER="${1:-}"
FAILED=0

echo "=== Version Validation Script ==="
echo ""

# Determine project type
PROJECT_TYPE=""
if [[ -f ".claude-plugin/marketplace.json" ]]; then
  PROJECT_TYPE="claude-marketplace"
  echo "Project type: Claude Plugin Marketplace"
elif [[ -f "pyproject.toml" ]]; then
  PROJECT_TYPE="python"
  echo "Project type: Python"
elif [[ -f "package.json" ]]; then
  PROJECT_TYPE="node"
  echo "Project type: Node.js"
elif [[ -f "Cargo.toml" ]]; then
  PROJECT_TYPE="rust"
  echo "Project type: Rust"
else
  echo "⚠️  Unknown project type - skipping validation"
  exit 0
fi

echo ""

# Claude Marketplace validation
if [[ "$PROJECT_TYPE" == "claude-marketplace" ]]; then
  echo "=== Claude Marketplace Validation ==="

  # Get ecosystem version
  if ! ECOSYSTEM_VERSION=$(jq -r '.metadata.version' .claude-plugin/marketplace.json 2>/dev/null); then
    echo "❌ Failed to parse ecosystem version from marketplace.json"
    exit 1
  fi

  echo "Ecosystem version: $ECOSYSTEM_VERSION"
  echo ""

  # Check each plugin
  echo "Checking plugin versions..."
  while IFS=: read -r name marketplace_version; do
    if [[ -f "plugins/$name/.claude-plugin/plugin.json" ]]; then
      ACTUAL_VERSION=$(jq -r '.version' "plugins/$name/.claude-plugin/plugin.json" 2>/dev/null || echo "PARSE_ERROR")

      if [[ "$ACTUAL_VERSION" == "PARSE_ERROR" ]]; then
        echo "  ❌ $name: Failed to parse version from plugin.json"
        FAILED=1
      elif [[ "$marketplace_version" != "$ACTUAL_VERSION" ]]; then
        echo "  ❌ $name: VERSION MISMATCH"
        echo "      Marketplace: $marketplace_version"
        echo "      Actual:      $ACTUAL_VERSION"
        FAILED=1
      else
        echo "  ✓ $name: $marketplace_version"
      fi
    else
      echo "  ⚠️  $name: plugin.json not found at plugins/$name/.claude-plugin/plugin.json"
    fi
  done < <(jq -r '.plugins[] | "\(.name):\(.version)"' .claude-plugin/marketplace.json)

  echo ""

  # Check CHANGELOG
  if [[ -f "CHANGELOG.md" ]]; then
    echo "Checking CHANGELOG.md..."
    if grep -q "\[$ECOSYSTEM_VERSION\]" CHANGELOG.md; then
      echo "  ✓ CHANGELOG has entry for $ECOSYSTEM_VERSION"

      # Check if marked as Unreleased
      if grep -q "\[$ECOSYSTEM_VERSION\] - Unreleased" CHANGELOG.md; then
        echo "  ℹ️  Version marked as 'Unreleased' - update date before release"
      fi
    else
      echo "  ❌ CHANGELOG missing entry for version $ECOSYSTEM_VERSION"
      FAILED=1
    fi
  else
    echo "  ⚠️  CHANGELOG.md not found"
  fi

  echo ""
fi

# Python validation
if [[ "$PROJECT_TYPE" == "python" ]]; then
  echo "=== Python Project Validation ==="

  # Get version from pyproject.toml
  if ! TOML_VERSION=$(grep "^version" pyproject.toml | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 2>/dev/null); then
    echo "❌ Failed to parse version from pyproject.toml"
    exit 1
  fi

  echo "pyproject.toml version: $TOML_VERSION"

  # Check __version__ in source if exists
  if [[ -d "src" ]]; then
    VERSION_PY=$(find src -name "__init__.py" -exec grep -l "__version__" {} \; 2>/dev/null | head -1)
    if [[ -n "$VERSION_PY" ]]; then
      CODE_VERSION=$(grep "__version__" "$VERSION_PY" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "")

      if [[ -n "$CODE_VERSION" ]]; then
        if [[ "$CODE_VERSION" == "$TOML_VERSION" ]]; then
          echo "  ✓ __version__ matches: $CODE_VERSION"
        else
          echo "  ❌ __version__ MISMATCH"
          echo "      pyproject.toml: $TOML_VERSION"
          echo "      __version__:    $CODE_VERSION"
          FAILED=1
        fi
      fi
    fi
  fi

  echo ""
fi

# Summary
echo "=== Validation Summary ==="
if [[ $FAILED -eq 0 ]]; then
  echo "✅ All version checks PASSED"
  exit 0
else
  echo "❌ Version validation FAILED"
  echo ""
  echo "Fix the version mismatches before proceeding."
  exit 1
fi
