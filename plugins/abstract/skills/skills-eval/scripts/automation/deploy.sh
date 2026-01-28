#!/bin/bash
# Deployment script for Skills Evaluation Framework
# Sets up and validates the evaluation environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_EVAL_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
MODULAR_SKILLS_DIR="$(dirname "$SKILLS_EVAL_DIR")/modular-skills"

echo " Setting up Skills Evaluation Framework..."

# validate directories exist
if [[ ! -d "$SKILLS_EVAL_DIR" ]]; then
    echo " Skills evaluation directory not found: $SKILLS_EVAL_DIR"
    exit 1
fi

if [[ ! -d "$MODULAR_SKILLS_DIR" ]]; then
    echo " Modular skills directory not found: $MODULAR_SKILLS_DIR"
    exit 1
fi

# Make all tools executable
echo " Making scripts executable..."
find "$SKILLS_EVAL_DIR/scripts" -type f -name "*" -exec chmod +x {} \;
find "$MODULAR_SKILLS_DIR/scripts" -type f -name "*" -exec chmod +x {} \;

# Test basic functionality
echo "Testing scripts..."

# Test skills-auditor
if [[ -x "$SKILLS_EVAL_DIR/scripts/skills-auditor" ]]; then
    if "$SKILLS_EVAL_DIR/scripts/skills-auditor" --help > /dev/null 2>&1; then
        echo " skills-auditor working"
    else
        echo "[WARN]  skills-auditor may have issues"
    fi
else
    echo " skills-auditor not executable"
fi

# Test modular-skills scripts
for tool in skill-analyzer token-estimator module_validator; do
    if [[ -x "$MODULAR_SKILLS_DIR/scripts/$tool" ]]; then
        echo " $tool executable"
    else
        echo " $tool not executable"
    fi
done

echo ""
echo " Deployment complete!"
echo ""
echo "Quick start commands:"
echo "  $SKILLS_EVAL_DIR/scripts/skills-auditor --discover"
echo "  $MODULAR_SKILLS_DIR/scripts/skill-analyzer --path your-skill.md"
echo "  $SKILLS_EVAL_DIR/scripts/compliance-checker --help"
