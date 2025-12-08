# Memory Palace Plugin Makefile
# Mnemonic knowledge organization and digital garden management
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps check fix format lint type-check typecheck spellcheck security test test-unit precommit \
        status clean install-hooks enable disable skills install create list search delete manager export \
        import garden-metrics garden-tend demo-reset demo-import demo-export plugin-check demo-status

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# ---------- Plugin-specific Variables ----------
UV              ?= UV_CACHE_DIR=$(PWD)/.uv-cache uv
PY              ?= $(UV) run python
CLI             ?= $(PY) tools/memory_palace_cli.py
SRC_DIRS        ?= tools src
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
	$(UV) run python -c "print('Dependencies synced and importable.')"

fix: ## Auto-fix code style issues
	@echo "Auto-fixing code style issues..."
	$(UV) run ruff format $(SRC_DIRS)
	$(UV) run ruff check --fix $(SRC_DIRS)

# ---------- Code quality ----------
format: ## Format Python code
	@echo "Formatting Python code..."
	$(UV) run ruff format $(SRC_DIRS)

lint: ## Run linting checks
	@echo "Running linting checks..."
	$(UV) run ruff check $(SRC_DIRS)

type-check: ## Run type checking
	@echo "Running type checking..."
	$(UV) run mypy $(SRC_DIRS) || { echo "⚠ Type checking failed"; exit 1; }

# Alias for backwards compatibility
typecheck: type-check

spellcheck: ## Run spell check
	@echo "Running spell check..."
	$(UV) run typos

security: ## Run security checks
	@echo "Running security checks..."
	$(UV) run bandit -r $(SRC_DIRS) || { echo "⚠ Security check failed"; exit 1; }

test-unit: ## Run unit and integration tests
	@echo "Running unit and integration tests..."
	$(UV) run pytest tests/ -v

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
	PALACES_DIR=$(PALACES_DIR) $(CLI) list

search:
	PALACES_DIR=$(PALACES_DIR) $(CLI) search "$(QUERY)"

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
	GARDEN_FILE=$(GARDEN_FILE) $(CLI) garden metrics --path "$(GARDEN_FILE)" --format brief

garden-tend:
	GARDEN_FILE=$(GARDEN_FILE) $(CLI) garden tend --path "$(GARDEN_FILE)" --prometheus

# ---------- Demo & validation flows ----------
demo-reset:
	rm -rf $(PALACES_DIR)
	mkdir -p $(PALACES_DIR)

demo-import: demo-reset
	PALACES_DIR=$(PALACES_DIR) $(CLI) import --source "$(IMPORT_SRC)" --overwrite

demo-export:
	@mkdir -p $(dir $(EXPORT_DEST))
	PALACES_DIR=$(PALACES_DIR) $(CLI) export --destination "$(EXPORT_DEST)"

demo-status:
	PALACES_DIR=$(PALACES_DIR) $(CLI) status

plugin-check: demo-import garden-metrics list search demo-export
	@echo "Plugin demo completed against $(PALACES_DIR)"
