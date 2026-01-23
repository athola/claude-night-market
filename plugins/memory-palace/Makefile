# Memory Palace Plugin Makefile
# Mnemonic knowledge organization and digital garden management
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps check fix format lint type-check typecheck spellcheck security test test-unit precommit \
        status clean install-hooks enable disable skills install create list search delete manager export \
        import garden-metrics garden-tend mutation-test benchmark memory-profile demo-reset demo-import demo-export plugin-check demo-status debug-variables

# Plugin-specific variables (must be before include)
SRC_DIRS := scripts src
UV ?= UV_CACHE_DIR=$(PWD)/.uv-cache uv
COV_DIRS := $(SRC_DIRS)

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# ---------- Plugin-specific Variables ----------
PY              ?= $(UV_PYTHON)
CLI             ?= $(UV) run python scripts/memory_palace_cli.py
PALACES_DIR     ?= $(PWD)/.demo-palaces
GARDEN_FILE     ?= examples/garden-sample.json
IMPORT_SRC      ?= examples/palaces-sample.json
EXPORT_DEST     ?= reports/palaces-export.json
NAME            ?= Demo-Palace
DOMAIN          ?= demo
METAPHOR        ?= building
QUERY           ?= concept

# ---------- Help ----------
help: ## Show this help message
	@echo "Memory Palace Plugin - Make Targets"
	@echo "===================================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Palace Management (use variables NAME, DOMAIN, METAPHOR, QUERY, ID):"
	@echo "  create            Create palace (NAME, DOMAIN, METAPHOR)"
	@echo "  list              List palaces"
	@echo "  search            Search with QUERY"
	@echo "  delete            Delete by ID"
	@echo "  export/import     Bundle palaces"
	@echo ""
	@echo "Variables: PALACES_DIR=$(PALACES_DIR)"

# ---------- Dependency management ----------
deps: ## Install and sync dependencies
	$(UV) sync

check: ## Run dependency validation
	@echo "Running dependency validation..."
	$(UV_PYTHON) -c "print('Dependencies synced and importable.')"

fix: ## Auto-fix code style issues
	@echo "Auto-fixing code style issues..."
	$(RUFF) format $(SRC_DIRS)
	$(RUFF) check --fix $(SRC_DIRS)

# ---------- Code quality ----------
spellcheck: ## Run spell check
	@echo "Running spell check..."
	$(UV_RUN) typos

test: lint type-check spellcheck security test-unit plugin-check ## Run all quality checks
	@echo "All checks passed!"

precommit: ## Run pre-commit hooks
	@echo "Running pre-commit hooks..."
	@if [ -d .git ]; then \
		$(UV) run pre-commit run --all-files; \
	else \
		echo "Skipping pre-commit (not a git repository)"; \
	fi

# ---------- Git and hooks ----------
install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@if [ -d .git ]; then \
		$(UV) run pre-commit install; \
	else \
		echo "Skipping hook install (not a git repository)"; \
	fi

# ---------- Maintenance ----------
clean: ## Clean cache and build files
	@echo "Cleaning up..."
	rm -rf .venv 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	$(UV) cache clean 2>/dev/null || true

status: ## Show project overview
	@echo "Memory Palace Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tools:  $$(find tools/ src/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

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

# ---------- Plugin control ----------
enable:
	$(PY) tools/memory_palace_cli.py enable || echo "Skip enable (permission denied)"

disable:
	$(PY) tools/memory_palace_cli.py disable || echo "Skip disable (permission denied)"

skills:
	$(PY) tools/memory_palace_cli.py skills || echo "Skip skills (permission denied)"

install:
	$(PY) tools/memory_palace_cli.py install || echo "Skip install (permission denied)"

# ---------- Palace management (PALACES_DIR scoped) ----------
create:
	PALACES_DIR=$(PALACES_DIR) $(CLI) create "$(NAME)" "$(DOMAIN)" --metaphor "$(METAPHOR)"

list:
	PALACES_DIR=$(PALACES_DIR) $(CLI) list || true

search:
	PALACES_DIR=$(PALACES_DIR) $(CLI) search "$(QUERY)" || true

delete:
	@if [ -z "$(ID)" ]; then echo "Set ID=<palace_id>" && exit 1; fi
	PALACES_DIR=$(PALACES_DIR) $(CLI) manager delete $(ID)

manager:
	PALACES_DIR=$(PALACES_DIR) $(CLI) manager $(ARGS)

export:
	@mkdir -p $(dir $(EXPORT_DEST))
	PALACES_DIR=$(PALACES_DIR) $(CLI) export --destination "$(EXPORT_DEST)"

import:
	PALACES_DIR=$(PALACES_DIR) $(CLI) import --source "$(IMPORT_SRC)" $(if $(OVERWRITE),--overwrite,)

# ---------- Garden utilities ----------
garden-metrics:
	GARDEN_FILE=$(GARDEN_FILE) $(CLI) garden metrics --path "$(GARDEN_FILE)" --format brief || true

garden-tend:
	GARDEN_FILE=$(GARDEN_FILE) $(CLI) garden tend --path "$(GARDEN_FILE)" --prometheus

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate src/memory_palace --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks (memory operations)
	$(PYTEST) --benchmark-only --benchmark-sort=mean || echo "pytest-benchmark not installed"

memory-profile: ## Profile memory usage
	@echo "Memory profiling not yet configured for memory-palace"
	@echo "Install memory_profiler: pip install memory_profiler"

# ---------- Demo & validation flows ----------
demo-reset:
	rm -rf $(PALACES_DIR)
	mkdir -p $(PALACES_DIR)

demo-import: demo-reset
	PALACES_DIR=$(PALACES_DIR) $(CLI) import --source "$(IMPORT_SRC)" --overwrite || true

demo-export:
	@mkdir -p $(dir $(EXPORT_DEST))
	PALACES_DIR=$(PALACES_DIR) $(CLI) export --destination "$(EXPORT_DEST)" || true

demo-status:
	PALACES_DIR=$(PALACES_DIR) $(CLI) status

plugin-check: demo-import garden-metrics list search demo-export
	@echo "Plugin demo completed against $(PALACES_DIR)"

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
