# Sanctum Plugin Makefile
# Git workflow management, commits, and PR preparation
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help install test test-unit test-integration test-all test-cov test-bdd test-git lint format \
        type-check security qa clean watch-test docs ci-test ci-build install-hooks profile-test \
        quick-check status deps demo-commit demo-pr-prep demo-git-workspace demo-skills plugin-check

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Plugin-specific variables
SRC_DIRS ?= src tests

# Default target
help: ## Show this help message
	@echo "Sanctum Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

# ---------- Installation ----------
install: ## Install development dependencies
	uv sync --dev

deps: ## Sync dependencies
	uv sync

# ---------- Testing ----------
test: ## Run all tests
	uv run pytest

test-unit: ## Run only unit tests
	uv run pytest -m "unit or not integration"

test-integration: ## Run only integration tests
	uv run pytest -m "integration"

test-all: ## Run all tests with detailed output
	uv run pytest -v --tb=short

test-cov: ## Run tests with coverage report
	uv run pytest --cov=src/sanctum --cov-report=term-missing --cov-report=html

test-bdd: ## Run BDD-style tests
	uv run pytest -m "bdd" -v

test-git: ## Run Git-related tests
	uv run pytest -m "git" -v

# ---------- Code Quality ----------
lint: ## Run linting checks
	uv run ruff check . || { echo "⚠ Linting failed"; exit 1; }

format: ## Format code
	uv run ruff format .

type-check: ## Run type checking
	uv run mypy . || { echo "⚠ Type checking failed"; exit 1; }

security: ## Run security checks
	uv run bandit -r src/ || { echo "⚠ Security check failed"; exit 1; }

qa: lint type-check test-cov ## Run all quality assurance checks

# ---------- CI/CD ----------
ci-test: ## Run tests in CI mode
	uv run pytest --cov=src/sanctum --cov-report=xml --cov-report=term --junit-xml=junit.xml

ci-build: ## Build package for CI
	uv build

# ---------- Development Helpers ----------
watch-test: ## Watch for changes and run tests
	uv run pytest-watch -- tests/ || echo "pytest-watch not installed"

quick-check: ## Run quick lint and test checks
	@echo "Running quick checks..."
	uv run ruff check . --quiet
	uv run pytest -x -q

profile-test: ## Profile test execution
	uv run pytest --profile --profile-svg || echo "pytest-profiling not installed"

docs: ## Generate documentation
	@echo "Documentation is in markdown files in the docs/ directory"

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		uv run pre-commit install; \
	else \
		echo "Create .pre-commit-config.yaml first"; \
	fi

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache dist build security-report.json junit.xml 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Sanctum Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

# ---------- Demo/Dogfood Targets ----------
demo-commit: ## Demo commit message generation workflow
	@echo "=== Sanctum Commit Demo ==="
	@echo "Demonstrating commit-messages skill workflow..."
	@echo ""
	@echo "Step 1: Gather context"
	@git status --short | head -10 || echo "(no changes)"
	@echo ""
	@echo "Step 2: Analyze changes"
	@git diff --stat HEAD 2>/dev/null | head -10 || echo "(no staged changes)"
	@echo ""
	@echo "Step 3: Generate commit message format"
	@echo "  Type: feat|fix|docs|style|refactor|test|chore"
	@echo "  Scope: (optional component)"
	@echo "  Subject: imperative mood, no period"
	@echo ""
	@echo "Example: feat(skills): add commit message generation"
	@echo ""
	@echo "Commit demo complete. Use /sanctum:commit-msg for full workflow."

demo-pr-prep: ## Demo PR preparation workflow
	@echo "=== Sanctum PR Prep Demo ==="
	@echo "Demonstrating pr-prep skill workflow..."
	@echo ""
	@echo "Step 1: Branch analysis"
	@git rev-parse --abbrev-ref HEAD
	@git log --oneline -5
	@echo ""
	@echo "Step 2: Change summary"
	@git diff --stat HEAD~3..HEAD 2>/dev/null | head -10 || git diff --stat HEAD~1..HEAD
	@echo ""
	@echo "Step 3: PR template structure"
	@echo "  ## Summary"
	@echo "  ## Changes"
	@echo "  ## Test Plan"
	@echo "  ## Checklist"
	@echo ""
	@echo "PR prep demo complete. Use /sanctum:pr for full workflow."

demo-git-workspace: ## Demo git workspace review
	@echo "=== Sanctum Git Workspace Demo ==="
	@echo "Demonstrating git-workspace-review skill..."
	@echo ""
	@echo "Repository state:"
	@git status -sb
	@echo ""
	@echo "Recent activity:"
	@git log --oneline --since="1 week ago" | head -10 || git log --oneline -5
	@echo ""
	@echo "Branches:"
	@git branch -a | head -10
	@echo ""
	@echo "Git workspace demo complete. Use sanctum:git-workspace-review for full analysis."

demo-skills: ## Validate sanctum skill structure
	@echo "=== Sanctum Skills Demo ==="
	@echo "Git workflow skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  commit-messages:     $$(test -f skills/commit-messages/SKILL.md && echo '✓' || echo '✗')"
	@echo "  pr-prep:             $$(test -f skills/pr-prep/SKILL.md && echo '✓' || echo '✗')"
	@echo "  git-workspace-review: $$(test -f skills/git-workspace-review/SKILL.md && echo '✓' || echo '✗')"
	@echo "  doc-updates:         $$(test -f skills/doc-updates/SKILL.md && echo '✓' || echo '✗')"
	@echo "  version-updates:     $$(test -f skills/version-updates/SKILL.md && echo '✓' || echo '✗')"

plugin-check: demo-commit demo-pr-prep demo-git-workspace demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Sanctum Plugin Check Complete ==="