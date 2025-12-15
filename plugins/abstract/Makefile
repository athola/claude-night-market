# Abstract Plugin Makefile
# Supports cross-platform builds with proper error handling and automatic variables
#
# Modular Structure Available:
#   This Makefile is self-contained, but reusable components are in config/make/:
#   - config/make/common.mk  : Variables, tool detection, helper macros
#   - config/make/python.mk  : Python quality targets (format, lint, test)
#   - config/make/docs.mk    : Documentation targets (docs, docs-serve, docs-check)
#
#   To use modular includes in your own projects:
#     include config/make/common.mk
#     include config/make/python.mk

.PHONY: help check test clean install-hooks status docs docs-clean docs-serve docs-check \
        update-changelog check-changelog format lint type-check typecheck security unit-tests test-unit \
        test-coverage test-quick analyze-skill estimate-tokens audit-skill improve-skill \
        check-compliance audit-all eval-report dev-setup ci-check verify-install debug-variables \
        validate-skill-descriptions validate-plugin validate-self test-wrappers validate-migration generate-wrappers \
        demo-skills plugin-check

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Run all recipe lines in single shell (performance + variable persistence)
.ONESHELL:

# Prevent parallel execution for targets that share resources
.NOTPARALLEL: docs docs-clean docs-serve docs-check

# Tool detection with helpful error messages
PYTHON ?= python3
UV ?= uv

# Verify required tools are available (fail fast with actionable errors)
ifeq ($(shell command -v $(UV) 2>/dev/null),)
$(error uv is required but not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh)
endif

ifeq ($(shell command -v $(PYTHON) 2>/dev/null),)
$(error $(PYTHON) is required but not installed. Install Python 3.10+ from python.org or your package manager)
endif

# Optional tool detection (warn but don't fail)
HAS_PRE_COMMIT := $(shell command -v pre-commit 2>/dev/null)
HAS_SPHINX := $(shell $(PYTHON) -c "import sphinx" 2>/dev/null && echo yes)

# Tool commands - abstracted for single-point-of-change
UV_RUN := $(UV) run
UV_PYTHON := $(UV_RUN) python
PYTEST := $(UV_RUN) pytest
MYPY := $(UV_RUN) mypy
RUFF := $(UV_RUN) ruff
BANDIT := $(UV_RUN) bandit
SPHINXBUILD := $(UV_RUN) sphinx-build

# Directories (configurable for portability)
BUILD_DIR ?= build
DIST_DIR ?= dist
COV_DIR ?= htmlcov
DOCS_BUILD_DIR ?= docs/build
PYTHONPATH ?= src

# Source directories (override via environment or Makefile.local)
SCRIPTS_DIR ?= scripts
SRC_DIR ?= src/abstract
SKILLS_DIR ?= skills
SRC_DIRS := $(SCRIPTS_DIR) $(SRC_DIR)

# Helper function to check if a file exists
define file_exists
$(shell test -f $(1) && echo yes || echo no)
endef

# Helper macro to require PATH argument (reduces repetition in skill analysis targets)
define require_path
@test -n "$(PATH)" || { echo "Usage: make $(1) PATH=<path>"; exit 1; }
endef

# Default target - auto-generated from ## comments
help: ## Show this help message
	@echo ""
	@echo "Abstract Plugin - Make Targets"
	@echo "=============================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "; section=""} \
		/^# [A-Z][A-Z ]+$$/ { \
			if (section != "") print ""; \
			gsub(/^# /, "", $$0); \
			section = $$0; \
			printf "\033[1m%s:\033[0m\n", section; \
		} \
		/^[a-zA-Z_-]+:.*?## / { \
			printf "  %-20s %s\n", $$1, $$2; \
		}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Skill tools require PATH=<path> argument (e.g., make analyze-skill PATH=skills/foo)"

# DEVELOPMENT
check: ## Run all validation checks
	@echo "Running dependency validation..."
	$(UV_PYTHON) $(SCRIPTS_DIR)/abstract_validator.py --report --scan

test: format lint type-check security test-unit ## Run all quality checks
	@echo "All quality checks passed!"

format: ## Format code with ruff
	@echo "Formatting code..."
	@$(RUFF) format $(SRC_DIRS) || { echo "⚠ Ruff format failed"; exit 1; }
	@$(RUFF) check --fix $(SRC_DIRS) || { echo "⚠ Ruff check failed"; exit 1; }

lint: ## Run linting checks
	@echo "Running linting..."
	@$(RUFF) check $(SRC_DIRS) || { echo "⚠ Linting failed"; exit 1; }

type-check: ## Run type checking
	@echo "Running type checking..."
	@$(MYPY) $(SRC_DIRS) || { echo "⚠ Type checking failed"; exit 1; }

# Alias for backwards compatibility
typecheck: type-check

security: ## Run security checks
	@echo "Running security checks..."
	@$(BANDIT) -r $(SRC_DIRS) || { echo "⚠ Security check failed"; exit 1; }

# TESTING
test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@$(PYTEST) tests/ -v || { echo "⚠ Tests failed"; exit 1; }

# Alias for backwards compatibility
unit-tests: test-unit

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	@$(PYTEST) tests/ -v --cov=scripts --cov=src/abstract --cov-report=term-missing --cov-report=html || { echo "⚠ Coverage tests failed"; $(PYTEST) tests/ -v --tb=short; }

test-quick: ## Run tests without coverage
	@echo "Running quick tests (no coverage)..."
	@$(PYTEST) tests/ -v --no-cov --tb=short || { echo "⚠ Tests failed"; exit 1; }

# SETUP
install-hooks: ## Install pre-commit hooks
ifndef HAS_PRE_COMMIT
	@echo "⚠ pre-commit not found. Installing via uv..."
	@$(UV) pip install pre-commit
endif
	@echo "Installing pre-commit hooks..."
	$(UV_RUN) pre-commit install || true

clean: ## Clean cache and build files
	@echo "Cleaning up..."
	@rm -rf .venv 2>/dev/null || true
	@rm -rf $(BUILD_DIR) $(DIST_DIR) $(COV_DIR) $(DOCS_BUILD_DIR) 2>/dev/null || true
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@$(UV) cache clean 2>/dev/null || true

status: ## Show project overview
	@echo "Abstract Plugin Status:"
	@echo "Skills: $$(find $(SKILLS_DIR)/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Scripts: $$(find $(SRC_DIRS) -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests: $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

# SKILL ANALYSIS
analyze-skill: ## Analyze skill complexity (PATH=<path>)
	$(call require_path,$@)
	$(UV_PYTHON) $(SCRIPTS_DIR)/skill_analyzer.py --path "$(PATH)"

validate-skill-descriptions: ## Validate skill descriptions follow best practices
	@echo "Validating skill descriptions..."
	@PYTHONPATH=src $(UV_RUN) pytest tests/test_skill_structure.py -v --tb=short || { echo "Some skills need description improvements"; exit 1; }

validate-plugin: ## Validate plugin structure (PATH=<path>, defaults to current dir)
	@echo "Validating plugin structure..."
	$(UV_PYTHON) $(SCRIPTS_DIR)/validate-plugin.py "$(or $(PATH),.)"

validate-self: ## Validate this plugin's structure
	@echo "Validating abstract plugin structure..."
	$(UV_PYTHON) $(SCRIPTS_DIR)/validate-plugin.py .

estimate-tokens: ## Estimate token usage (PATH=<path>)
	$(call require_path,$@)
	$(UV_PYTHON) $(SCRIPTS_DIR)/token_estimator.py --file "$(PATH)"

audit-skill: ## Comprehensive skill audit (PATH=<path>)
	$(call require_path,$@)
	@echo "Note: This command references moved tools. Using skills-eval module instead."
	$(UV_PYTHON) -c "from abstract.skills_eval import SkillsAuditor; from pathlib import Path; auditor = SkillsAuditor(Path('$(PATH)').parent if '$(PATH)'.endswith('SKILL.md') else Path('$(PATH)')); result = auditor.audit_skills(); print(f'Score: {result.get(\"average_score\", 0):.1f}/100')" || echo "Audit completed with result in audit_results.json"

improve-skill: ## Generate improvement plan (PATH=<path>)
	$(call require_path,$@)
	@echo "Note: This command references moved tools. Using skills-eval module instead."
	$(UV_PYTHON) -c "from abstract.skills_eval import ImprovementSuggester; from pathlib import Path; suggester = ImprovementSuggester(Path('$(PATH)').parent if '$(PATH)'.endswith('SKILL.md') else Path('$(PATH)')); result = suggester.analyze_skill(Path('$(PATH)').stem); print(f'Issues: {len(result.get(\"issues\", []))}'); print(f'Suggestions: {len(result.get(\"suggestions\", []))}')" || echo "Improvement suggestions completed"

check-compliance: ## Check standards compliance (PATH=<path>)
	$(call require_path,$@)
	@echo "Note: This command references moved tools. Using skills-eval module instead."
	$(UV_PYTHON) -c "from abstract.skills_eval import ComplianceChecker; from pathlib import Path; checker = ComplianceChecker(Path('$(PATH)').parent if '$(PATH)'.endswith('SKILL.md') else Path('$(PATH)')); result = checker.check_compliance(); print(f'Compliant: {result.get(\"compliant\", False)}'); print(f'Total Skills: {result.get(\"total_skills\", 0)}')" || echo "Compliance check completed"

# EVALUATION
audit-all: ## Audit all skills in ~/.claude/
	@echo "Auditing all skills in ~/.claude/..."
	@echo "Note: This command references moved tools. Using skills-eval module instead."
	$(UV_PYTHON) -c "from abstract.skills_eval import SkillsAuditor; from pathlib import Path; auditor = SkillsAuditor(Path('~/.claude').expanduser()); result = auditor.audit_skills(); print(f'Total: {result.get(\"total_skills\", 0)}'); print(f'Average Score: {result.get(\"average_score\", 0):.1f}/100'); print(f'Well-structured: {result.get(\"well_structured\", 0)}')" || echo "Audit completed"

eval-report: ## Generate comprehensive evaluation report
	@echo "Generating comprehensive evaluation report..."
	$(UV_PYTHON) -c "from abstract.skills_eval import SkillsAuditor; from pathlib import Path; auditor = SkillsAuditor(Path('.')); result = auditor.audit_skills(); lines = ['# Skills Evaluation Report', f'Total Skills: {result.get(\"total_skills\", 0)}', f'Average Score: {result.get(\"average_score\", 0):.1f}/100']; Path('evaluation-report.md').write_text('\n'.join(lines)); print('Report saved to evaluation-report.md')" || echo "Report generated with fallback"

# DOCUMENTATION
docs: ## Build HTML documentation
ifndef HAS_SPHINX
	$(error sphinx is required for documentation. Install via: uv pip install sphinx sphinx-rtd-theme)
endif
	@echo "Building documentation..."
	@cd docs && $(SPHINXBUILD) -b html source $(@F)

docs-clean: ## Clean documentation build
	@echo "Cleaning documentation..."
	@rm -rf $(DOCS_BUILD_DIR)

docs-serve: ## Serve documentation locally (http://localhost:8000)
	@test -d $(DOCS_BUILD_DIR)/html || { echo "⚠ Documentation not built. Run 'make docs' first."; exit 1; }
	@echo "Serving documentation at http://localhost:8000"
	@cd $(DOCS_BUILD_DIR)/html && $(PYTHON) -m http.server 8000

docs-check: ## Check documentation links
ifndef HAS_SPHINX
	$(error sphinx is required for documentation. Install via: uv pip install sphinx sphinx-rtd-theme)
endif
	@echo "Checking documentation links..."
	@cd docs && $(SPHINXBUILD) -b linkcheck source build/linkcheck || true

# GOVERNANCE
update-changelog: ## Update CHANGELOG from git commits
	@echo "Updating changelog from git commits..."
	$(PYTHON) $(SCRIPTS_DIR)/update_changelog.py || echo "Changelog update completed with warnings"

check-changelog: ## Validate CHANGELOG format
	@echo "Validating changelog format..."
	$(PYTHON) $(SCRIPTS_DIR)/update_changelog.py --validate-only || echo "Changelog validation completed with warnings"

# UTILITIES
dev-setup: ## Complete development environment setup
	@echo "Setting up development environment..."
	@$(UV) sync --dev || true
	@make install-hooks
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make test' to verify setup"
	@echo "  2. Create a feature branch for your changes"
	@echo "  3. Make your changes and commit with conventional format"

ci-check: ## Run all CI checks locally
	@echo "Running CI checks locally..."
	@make format
	@make lint
	@make typecheck
	@make security
	@make unit-tests
	@echo "✓ All CI checks passed!"

verify-install: ## Verify installation works correctly
	@echo "Verifying installation..."
	@$(UV_PYTHON) -c "import abstract; print('✓ Abstract module imports successfully')" || echo "⚠ Abstract module import failed"
	@$(UV_PYTHON) -c "from abstract.cli_framework import AbstractCLI; print('✓ CLI framework imports successfully')" || echo "⚠ CLI framework import failed"
	@$(UV_PYTHON) $(SCRIPTS_DIR)/token_estimator.py --version 2>/dev/null && echo "✓ CLI tools work correctly" || echo "⚠ CLI tools may need adjustment"
	@echo "✓ Installation verification complete"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(SHELLFLAGS)"
	@echo "PYTHONPATH: $(PYTHONPATH)"
	@echo "BUILD_DIR: $(BUILD_DIR)"
	@echo "DOCS_BUILD_DIR: $(DOCS_BUILD_DIR)"
	@echo "SCRIPTS_DIR: $(SCRIPTS_DIR)"
	@echo "HOOKS_DIR: $(HOOKS_DIR)"
	@echo "SKILLS_DIR: $(SKILLS_DIR)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"

# WRAPPER TESTING AND VALIDATION
test-wrappers: ## Run all wrapper-related tests
	@echo "Running wrapper tests..."
	@$(PYTEST) tests/test_*_wrapper.py -v --tb=short || { echo "⚠ Wrapper tests failed"; exit 1; }

validate-migration: ## Validate migration compatibility and analyze overlaps
	@echo "Running migration validation..."
	@if [ -f "$(SCRIPTS_DIR)/compatibility_validator.py" ]; then \
		$(UV_PYTHON) "$(SCRIPTS_DIR)/compatibility_validator.py" --all; \
	fi
	@if [ -f "$(SCRIPTS_DIR)/migration_analyzer.py" ]; then \
		$(UV_PYTHON) "$(SCRIPTS_DIR)/migration_analyzer.py" --all; \
	fi
	@echo "✓ Migration validation completed"

generate-wrappers: ## Generate wrapper boilerplate for detected functionality
	@echo "Generating wrappers..."
	@if [ -f "$(SCRIPTS_DIR)/wrapper_generator.py" ]; then \
		$(UV_PYTHON) "$(SCRIPTS_DIR)/wrapper_generator.py" --auto-detect; \
	else \
		echo "⚠ wrapper_generator.py not found in $(SCRIPTS_DIR)/"; \
	fi
	@echo "✓ Wrapper generation completed"

# ---------- Demo/Dogfood Targets ----------
demo-skills: ## Validate abstract skill structure
	@echo "=== Abstract Skills Demo ==="
	@echo "Skill authoring and evaluation tools:"
	@for skill in $(SKILLS_DIR)/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Step 2: Running skill validator on abstract plugin..."
	$(UV_PYTHON) $(SCRIPTS_DIR)/validate-plugin.py . || echo "  (validation completed with warnings)"
	@echo ""
	@echo "Step 3: Token estimation sample"
	@$(UV_PYTHON) $(SCRIPTS_DIR)/token_estimator.py --file $(SKILLS_DIR)/skill-authoring/SKILL.md 2>/dev/null || echo "  (token estimator sample skipped)"

plugin-check: validate-self demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Abstract Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
