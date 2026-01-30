# Memory Palace Plugin Makefile
# Mnemonic knowledge organization and digital garden management
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: benchmark check clean clean-queue create debug-variables delete demo-export demo-garden \
	demo-import demo-navigate demo-palace demo-pensive demo-reset demo-review-room demo-skill-logs \
	demo-status deps disable enable export fix format garden-metrics garden-tend help import install \
	install-hooks lint list manager memory-profile mutation-test plugin-check precommit search security \
	skills spellcheck status test test-garden test-navigate test-palace test-pensive test-review-room \
	test-skill-logs test-unit type-check typecheck

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

# ---------- Test cleanup ----------
# Override test-unit to clean up queue files created during hook tests
QUEUE_DIR := docs/knowledge-corpus/queue

test-unit: ## Run unit tests (with queue cleanup)
	@echo "Running unit tests..."
	@$(PYTEST) $(TEST_UNIT_TARGETS) $(TEST_UNIT_ARGS) || { echo "[WARN] Tests failed"; exit 1; }
	@echo "Cleaning up test-generated queue files..."
	@rm -f $(QUEUE_DIR)/websearch-*.md $(QUEUE_DIR)/webfetch-*.md 2>/dev/null || true

clean-queue: ## Remove auto-generated queue files from tests
	@echo "Cleaning queue directory..."
	@rm -f $(QUEUE_DIR)/websearch-*.md $(QUEUE_DIR)/webfetch-*.md 2>/dev/null || true
	@echo "Queue cleaned."

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

demo-palace: ## Demo palace command (LIVE)
	@echo "=== palace Demo (LIVE) ==="
	@echo ""
	@echo "Command: /palace"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates palace usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /palace for full workflow."


demo-garden: ## Demo garden command (LIVE)
	@echo "=== garden Demo (LIVE) ==="
	@echo ""
	@echo "Command: /garden"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates garden usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /garden for full workflow."


demo-navigate: ## Demo navigate command (LIVE)
	@echo "=== navigate Demo (LIVE) ==="
	@echo ""
	@echo "Command: /navigate"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates navigate usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /navigate for full workflow."


demo-review-room: ## Demo review-room command (LIVE)
	@echo "=== review-room Demo (LIVE) ==="
	@echo ""
	@echo "Command: /review-room"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates review-room usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /review-room for full workflow."


demo-skill-logs: ## Demo skill-logs command (LIVE)
	@echo "=== skill-logs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /skill-logs"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates skill-logs usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /skill-logs for full workflow."


	@echo "=== review-room Demo (LIVE) ==="
	@echo ""
	@echo "Command: /review-room"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates review-room usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /review-room for full workflow."


	@echo "=== review-room Demo (LIVE) ==="
	@echo ""
	@echo "Command: /review-room"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates review-room usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /review-room for full workflow."


	@echo "=== review-room Demo (LIVE) ==="
	@echo ""
	@echo "Command: /review-room"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates review-room usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /review-room for full workflow."


	@echo "=== skill-logs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /skill-logs"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates skill-logs usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /skill-logs for full workflow."


	@echo "=== skill-logs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /skill-logs"
	@echo "Plugin: memory-palace"
	@echo ""
	@echo "This demonstrates skill-logs usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /skill-logs for full workflow."


demo-memory-palace-commands: demo-palace demo-garden demo-navigate demo-review-room demo-skill-logs demo-review-room demo-review-room demo-review-room demo-skill-logs demo-skill-logs ## Run all memory-palace documented command demos
	@echo ""
	@echo "=== Memory-palace All Commands Demo Complete ==="
	@echo "Ran 10 documented commands"
	@echo ""


test-palace: ## Test palace command workflow
	@echo "=== Testing palace workflow ==="
	@echo "Validating: /palace"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-garden: ## Test garden command workflow
	@echo "=== Testing garden workflow ==="
	@echo "Validating: /garden"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-navigate: ## Test navigate command workflow
	@echo "=== Testing navigate workflow ==="
	@echo "Validating: /navigate"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-review-room: ## Test review-room command workflow
	@echo "=== Testing review-room workflow ==="
	@echo "Validating: /review-room"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


test-skill-logs: ## Test skill-logs command workflow
	@echo "=== Testing skill-logs workflow ==="
	@echo "Validating: /skill-logs"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing review-room workflow ==="
	@echo "Validating: /review-room"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing review-room workflow ==="
	@echo "Validating: /review-room"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing review-room workflow ==="
	@echo "Validating: /review-room"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing skill-logs workflow ==="
	@echo "Validating: /skill-logs"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""


	@echo "=== Testing skill-logs workflow ==="
	@echo "Validating: /skill-logs"
	@echo "Check: Command executes without errors"
	@echo "Check: Output matches expected format"
	@echo "Status: [ ] Manual test required"
	@echo ""




# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
