# Leyline Plugin Makefile
# Infrastructure utilities: token tracking, quota management, plugin updates
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-coverage lint format type-check typecheck security clean \
        install-hooks status ci mutation-test benchmark memory-profile demo-tokens demo-quota \
        demo-skills demo-formatting demo-reinstall-all-plugins demo-update-all-plugins \
        demo-verify-plugin test-reinstall-all-plugins test-update-all-plugins test-verify-plugin \
        plugin-check debug-variables

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests scripts
COV_DIRS := src/leyline
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
TEST_UNIT_ARGS := -v -m "not integration"

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Default target
help: ## Show this help message
	@echo "Leyline Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	$(UV) sync

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) tests/ -v

# ---------- CI ----------
ci: lint type-check test ## Run CI pipeline
	@echo "CI pipeline completed!"

# ---------- Maintenance ----------
clean: ## Clean up generated files
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Leyline Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Source:   $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(SHELLFLAGS)"
	@echo "PYTHONPATH: $(PYTHONPATH)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"
	@echo "BANDIT_TARGETS: $(BANDIT_TARGETS)"
	@echo "COV_DIRS: $(COV_DIRS)"
	@echo "PYTEST_TARGETS: $(PYTEST_TARGETS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -f .pre-commit-config.yaml ]; then \
		$(UV_RUN) pre-commit install; \
	else \
		echo "No .pre-commit-config.yaml found"; \
	fi

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate src/leyline --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks (token estimation)
	$(PYTEST) --benchmark-only --benchmark-sort=mean || echo "pytest-benchmark not installed"

memory-profile: ## Profile memory usage
	@if python3 -c "import memory_profiler" 2>/dev/null; then \
		$(UV_RUN) python3 -m memory_profiler scripts/*.py; \
	else \
		echo "Install memory_profiler: pip install memory_profiler"; \
	fi

# ---------- Demo/Dogfood Targets ----------
demo-tokens: ## Demo token estimation on leyline source
	@echo "=== Leyline Token Demo ==="
	@echo "Demonstrating token tracking capabilities..."
	@echo ""
	@echo "Step 1: Source code metrics"
	@echo "Python files: $$(find src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Total lines: $$(find src/ -name '*.py' -exec cat {} \; 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 2: Token module check"
	@$(UV_RUN) python -c "from leyline.tokens import estimate_tokens; print(f'Token estimator available')" 2>/dev/null || echo "  (token module not loaded)"
	@echo ""
	@echo "Token demo complete."

demo-quota: ## Demo quota tracking
	@echo "=== Leyline Quota Demo ==="
	@echo "Demonstrating quota tracking capabilities..."
	@echo ""
	@echo "Step 1: Quota tracker check"
	@$(UV_RUN) python -c "from leyline.quota_tracker import QuotaTracker; print('QuotaTracker available')" 2>/dev/null || echo "  (quota tracker not loaded)"
	@echo ""
	@echo "Step 2: MECW module check"
	@$(UV_RUN) python -c "from leyline.mecw import *; print('MECW utilities available')" 2>/dev/null || echo "  (MECW module not loaded)"
	@echo ""
	@echo "Quota demo complete."

demo-skills: ## Validate leyline skill structure
	@echo "=== Leyline Skills Demo ==="
	@echo "Infrastructure skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"
	@echo ""
	@echo "Commands:"
	@find commands/ -name "*.md" 2>/dev/null | wc -l | xargs -I{} echo "  {} commands defined"

demo-formatting: ## Validate markdown-formatting skill structure
	@echo "=== Markdown Formatting Skill Demo ==="
	@echo "Checking skill structure..."
	@test -f skills/markdown-formatting/SKILL.md && \
		echo "  SKILL.md: OK" || echo "  SKILL.md: MISSING"
	@test -f skills/markdown-formatting/modules/wrapping-rules.md && \
		echo "  wrapping-rules.md: OK" || echo "  wrapping-rules.md: MISSING"
	@echo ""
	@echo "Frontmatter:"
	@head -10 skills/markdown-formatting/SKILL.md | grep -E '^(name|category|estimated_tokens):' | sed 's/^/  /'
	@echo ""
	@echo "Checking prose compliance (lines > 80 chars outside code blocks):"
	@$(PYTHON) -c "\
	in_code = False; violations = 0; \
	[exec('in_code = not in_code') if l.startswith('\`\`\`') \
	else exec('violations += 1') if not in_code and len(l.rstrip()) > 80 \
	and not l.startswith('|') and not l.startswith('---') \
	else None for l in open('skills/markdown-formatting/SKILL.md')]; \
	print(f'  {violations} violations found')" 2>/dev/null || echo "  (python3 check skipped)"
	@echo ""
	@echo "Formatting skill demo complete."

demo-reinstall-all-plugins: ## Demo reinstall-all-plugins command (LIVE)
	@echo "=== Leyline Reinstall All Plugins Demo (LIVE) ==="
	@echo ""
	@echo "Scanning installed plugins..."
	@find ../../plugins/ -maxdepth 1 -mindepth 1 -type d | sort | while read dir; do \
		name=$$(basename "$$dir"); \
		has_manifest=$$(test -f "$$dir/plugin.json" -o -f "$$dir/openpackage.yml" && echo "OK" || echo "MISSING"); \
		echo "  $$name: manifest=$$has_manifest"; \
	done
	@echo ""
	@echo "Use /leyline:reinstall-all-plugins for full reinstall workflow."

demo-update-all-plugins: ## Demo update-all-plugins command (LIVE)
	@echo "=== Leyline Update All Plugins Demo (LIVE) ==="
	@echo ""
	@echo "Plugin versions:"
	@for dir in ../../plugins/*/; do \
		name=$$(basename "$$dir"); \
		ver=$$(grep -m1 'version' "$$dir/openpackage.yml" 2>/dev/null | awk '{print $$2}' || echo "?"); \
		echo "  $$name: $$ver"; \
	done
	@echo ""
	@echo "Use /leyline:update-all-plugins for full update workflow."

demo-verify-plugin: ## Demo verify-plugin attestation check (LIVE)
	@echo "=== Leyline Verify Plugin Demo (LIVE) ==="
	@echo ""
	@echo "Verifying leyline plugin structure..."
	@test -f openpackage.yml && echo "  openpackage.yml: OK" || echo "  openpackage.yml: MISSING"
	@test -d skills && echo "  skills/: OK ($$(find skills/ -name 'SKILL.md' | wc -l) skills)" || echo "  skills/: MISSING"
	@test -d src && echo "  src/: OK ($$(find src/ -name '*.py' | wc -l) files)" || echo "  src/: MISSING"
	@test -d tests && echo "  tests/: OK ($$(find tests/ -name 'test_*.py' | wc -l) tests)" || echo "  tests/: MISSING"
	@echo ""
	@echo "Use /leyline:verify-plugin for full attestation verification."

test-reinstall-all-plugins: ## Test reinstall-all-plugins (runs plugin health tests)
	$(PYTEST) tests/test_plugin_health.py -v || \
		$(PYTEST) tests/ -v -k "plugin_health or reinstall"

test-update-all-plugins: ## Test update-all-plugins (runs update workflow tests)
	$(PYTEST) tests/test_update_all_plugins.py -v || \
		$(PYTEST) tests/ -v -k "update_all"

test-verify-plugin: ## Test verify-plugin (runs plugin health tests)
	$(PYTEST) tests/test_plugin_health.py -v || \
		$(PYTEST) tests/ -v -k "plugin_health or verify"

plugin-check: demo-tokens demo-quota demo-skills demo-formatting demo-reinstall-all-plugins demo-update-all-plugins demo-verify-plugin status ## Run all demo workflows
	@echo ""
	@echo "=== Leyline Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
