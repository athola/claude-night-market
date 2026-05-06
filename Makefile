# Claude Night Market - Root Makefile
# Delegates to plugin Makefiles for build operations

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Local tool cache (avoids permission issues with default locations)
UV_TOOL_DIR ?= $(abspath .)/.uv-tools
PATH := $(UV_TOOL_DIR)/ruff/bin:$(PATH)

# Plugin directories
PLUGINS_DIR := plugins

# All plugin directories for iteration (auto-detected)
PLUGIN_MAKEFILES := $(wildcard $(PLUGINS_DIR)/*/Makefile)
ALL_PLUGINS := $(patsubst %/Makefile,%,$(PLUGIN_MAKEFILES))
ALL_PLUGIN_NAMES := $(notdir $(ALL_PLUGINS))

# Generate delegation targets dynamically for all plugins with Makefiles.
# This replaces ~70 lines of manual per-plugin delegation with a single
# template that auto-covers any plugin that has a Makefile.
define plugin_delegation
.PHONY: $(1) $(1)-%
$(1)-%:
	@$$(MAKE) -C $$(PLUGINS_DIR)/$(1) $$*
$(1):
	@$$(MAKE) -C $$(PLUGINS_DIR)/$(1)
endef
$(foreach p,$(ALL_PLUGIN_NAMES),$(eval $(call plugin_delegation,$(p))))

.PHONY: help all test lint typecheck clean status validate-all plugin-check check-examples docs-sync-check demo verify-deferred-capture supply-chain-scan

# Default target
all: lint test ## Run lint and test across all plugins

help: ## Show this help message
	@echo ""
	@echo "Claude Night Market - Make Targets"
	@echo "==================================="
	@echo ""
	@echo "Root targets (run on ALL code, not just changed files):"
	@echo "  help              Show this help message"
	@echo "  all               Run lint and test across all plugins"
	@echo "  test              Run tests in all plugins (ALL code)"
	@echo "  lint              Run linting in all plugins (ALL code)"
	@echo "  typecheck         Run type checking in all plugins (ALL code)"
	@echo "  status            Show status of all plugins"
	@echo "  clean             Clean all plugin artifacts"
	@echo "  validate-all      Validate all plugin structures"
	@echo "  supply-chain-scan Scan lockfiles for compromised packages"
	@echo "  plugin-check      Run demo/dogfood checks across all plugins"
	@echo "  check-examples    Verify all plugins have proper examples"
	@echo ""
	@echo "Plugin delegation (run with 'make <plugin>-<target>'):"
	@echo "  Detected plugins: $(ALL_PLUGIN_NAMES)"
	@echo ""
	@echo "Examples:"
	@echo "  make abstract-help      Show abstract plugin targets"
	@echo "  make pensive-test       Run pensive tests"
	@echo "  make sanctum-lint       Run sanctum linting"
	@echo "  make egregore-check     Run egregore checks"
	@echo ""
	@echo "Or use 'make -C <plugin-dir> <target>' directly"

# Aggregate targets
# NOTE: These targets run on ALL code (not just changed files)
# For changed-files-only checks, use pre-commit hooks or run scripts with --changed
test: ## Run tests in all plugins (ALL code, not just changed)
	@./scripts/run-plugin-tests.sh --all

lint: ## Run linting on all plugins (ALL code, not just changed)
	@echo "=== Running Lint on ALL Code ==="
	@echo ""
	@echo ">>> Running ruff format on plugins/..."
	@uv run ruff format --config pyproject.toml plugins/ || (echo "Ruff format failed" && exit 1)
	@echo "Ruff format passed"
	@echo ""
	@echo ">>> Running ruff check with auto-fix on plugins/..."
	@uv run ruff check --fix --config pyproject.toml plugins/ || (echo "Ruff check failed" && exit 1)
	@echo "Ruff check passed"
	@echo ""
	@echo ">>> Running ruff format again (to fix any formatting from check)..."
	@uv run ruff format --config pyproject.toml plugins/ || (echo "Ruff format failed" && exit 1)
	@echo "Ruff format passed"
	@echo ""
	@echo ">>> Running bandit security checks on plugins/..."
	@uv run bandit --quiet -c pyproject.toml -r plugins/ || (echo "Bandit failed" && exit 1)
	@echo "Bandit passed"
	@echo ""
	@echo "=== Lint Complete (All Code Checked) ==="

typecheck: ## Run type checking on all plugins (ALL code, not just changed)
	@./scripts/run-plugin-typecheck.sh --all

status: ## Show status of all plugins
	@echo "=== Plugin Status ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> $$plugin:"; \
		$(MAKE) -C $$plugin status 2>/dev/null || echo "  (status unavailable)"; \
	done

clean: ## Clean all plugin artifacts
	@echo "Cleaning all plugins..."
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo "Cleaning $$plugin..."; \
			$(MAKE) -C $$plugin clean 2>/dev/null || true; \
		fi; \
	done
	@echo "Done."

supply-chain-scan: ## Scan lockfiles for known compromised package versions and malicious artifacts
	@echo "=== Supply Chain Scan ==="
	@echo ""
	@python3 scripts/supply_chain_scan.py
	@echo ""
	@echo "=== Supply Chain Scan Complete ==="

validate-all: ## Validate all plugin structures
	@echo "=== Validating Plugin Structures ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> Validating $$plugin:"; \
		python3 plugins/abstract/scripts/validate_plugin.py $$plugin || echo "  (validation failed)"; \
	done

plugin-check: ## Run demo/dogfood checks across all plugins
	@echo "=== Running Plugin Checks (Dogfooding) ==="
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ] && grep -q "^plugin-check:" "$$plugin/Makefile"; then \
			echo ""; \
			echo ">>> $$plugin:"; \
			$(MAKE) -C $$plugin plugin-check 2>/dev/null || echo "  (plugin-check failed)"; \
		fi; \
	done
	@echo ""
	@echo "=== All Plugin Checks Complete ==="

check-examples: ## Verify all plugins have proper examples
	@echo "=== Checking Plugin Examples ==="
	@python3 tests/integration/test_all_plugin_examples.py --report
	@echo ""
	@echo "=== Example Check Complete ==="

docs-sync-check: ## Verify capabilities docs match plugin registrations
	@bash scripts/capabilities-sync-check.sh

check-json-utils: ## Verify inlined JSON utilities match scripts/shared/json_utils.sh
	@bash scripts/shared/check-json-utils-drift.sh

# ---------- Skrills binary (plugin bin/ support, v2.1.91+) ----------

SKRILLS_REPO ?= $(HOME)/skrills
SKRILLS_BIN := plugins/abstract/bin/skrills
SKRILLS_VERSION_FILE := plugins/abstract/bin/.skrills-version

.PHONY: skrills-build skrills-install skrills-verify skrills-clean

skrills-build: ## Build skrills from source (requires Rust toolchain)
	@if [ ! -d "$(SKRILLS_REPO)" ]; then \
		echo "Error: skrills repo not found at $(SKRILLS_REPO)"; \
		echo "Set SKRILLS_REPO=/path/to/skrills or clone it first"; \
		exit 1; \
	fi
	@echo "Building skrills..."
	@cargo build --manifest-path "$(SKRILLS_REPO)/Cargo.toml" --release -p skrills 2>&1 | tail -1
	@cp "$(SKRILLS_REPO)/target/release/skrills" "$(SKRILLS_BIN)"
	@chmod +x "$(SKRILLS_BIN)"
	@$(SKRILLS_BIN) --version 2>/dev/null | head -1 > "$(SKRILLS_VERSION_FILE)" || true
	@sha256sum "$(SKRILLS_BIN)" | cut -d' ' -f1 >> "$(SKRILLS_VERSION_FILE)"
	@echo "Installed: $(SKRILLS_BIN) ($$(cat $(SKRILLS_VERSION_FILE) | head -1))"

skrills-install: ## Copy pre-built skrills binary to plugin bin/
	@if [ -x "$(SKRILLS_REPO)/target/release/skrills" ]; then \
		cp "$(SKRILLS_REPO)/target/release/skrills" "$(SKRILLS_BIN)"; \
		chmod +x "$(SKRILLS_BIN)"; \
		echo "Installed: $(SKRILLS_BIN)"; \
	elif command -v skrills >/dev/null 2>&1; then \
		cp "$$(command -v skrills)" "$(SKRILLS_BIN)"; \
		chmod +x "$(SKRILLS_BIN)"; \
		echo "Installed from PATH: $(SKRILLS_BIN)"; \
	else \
		echo "No skrills binary found. Run 'make skrills-build' or 'cargo install skrills'"; \
		exit 1; \
	fi

skrills-verify: ## Verify skrills binary hash against pinned version
	@if [ ! -f "$(SKRILLS_VERSION_FILE)" ]; then \
		echo "No version file. Run 'make skrills-build' first."; exit 1; \
	fi
	@expected=$$(tail -1 "$(SKRILLS_VERSION_FILE)"); \
	actual=$$(sha256sum "$(SKRILLS_BIN)" | cut -d' ' -f1); \
	if [ "$$expected" = "$$actual" ]; then \
		echo "OK: hash matches ($$(head -1 $(SKRILLS_VERSION_FILE)))"; \
	else \
		echo "FAIL: hash mismatch (expected $$expected, got $$actual)"; exit 1; \
	fi

skrills-clean: ## Remove skrills binary from plugin bin/
	@rm -f "$(SKRILLS_BIN)" "$(SKRILLS_VERSION_FILE)"
	@echo "Cleaned: $(SKRILLS_BIN)"

# Validation with skrills fallback to Python
validate-skills: ## Validate skills (uses skrills if available, falls back to Python)
	@if [ -x "$(SKRILLS_BIN)" ]; then \
		$(SKRILLS_BIN) validate --skill-dir plugins --target claude; \
	elif command -v skrills >/dev/null 2>&1; then \
		skrills validate --skill-dir plugins --target claude; \
	else \
		echo "skrills not available, using Python fallback"; \
		uv run python scripts/check_plugin_hooks.py; \
	fi

analyze-skills: ## Analyze skill token usage and dependencies (skrills or Python)
	@if [ -x "$(SKRILLS_BIN)" ]; then \
		$(SKRILLS_BIN) analyze --skill-dir plugins; \
	elif command -v skrills >/dev/null 2>&1; then \
		skrills analyze --skill-dir plugins; \
	else \
		echo "skrills not available, using Python fallback"; \
		uv run python scripts/generate_dependency_map.py; \
	fi

# ---------- ClawHub / OpenClaw export ----------

CLAWHUB_DIR := clawhub

.PHONY: clawhub-export clawhub-export-top clawhub-validate clawhub-stats clawhub-clean
.PHONY: bridge-build bridge-clean a2a-cards a2a-list detect-framework cross-framework

clawhub-export: ## Export all skills to ClawHub/OpenClaw format
	@echo "=== Exporting skills to ClawHub format ==="
	@uv run python scripts/clawhub_export.py --output $(CLAWHUB_DIR)
	@uv run python scripts/clawhub_export.py --validate --output $(CLAWHUB_DIR)
	@echo "=== Export complete and validated ==="

clawhub-export-top: ## Export top 20 most marketable skills to ClawHub
	@echo "=== Exporting top 20 skills to ClawHub format ==="
	@uv run python scripts/clawhub_export.py --output $(CLAWHUB_DIR) --top 20
	@uv run python scripts/clawhub_export.py --validate --output $(CLAWHUB_DIR)
	@echo "=== Export complete and validated ==="

clawhub-validate: ## Validate existing ClawHub export
	@uv run python scripts/clawhub_export.py --validate --output $(CLAWHUB_DIR)

clawhub-stats: ## Show skill export statistics
	@uv run python scripts/clawhub_export.py --stats

clawhub-clean: ## Remove ClawHub export directory
	@rm -rf $(CLAWHUB_DIR)
	@echo "Cleaned $(CLAWHUB_DIR)/"

bridge-build: clawhub-export ## Build OpenClaw bridge plugin from export
	@echo "=== Building OpenClaw bridge plugin ==="
	@uv run python scripts/build_bridge.py
	@echo "=== Bridge plugin ready at bridge/openclaw/ ==="

bridge-clean: ## Clean bridge plugin skills
	@rm -rf bridge/openclaw/skills bridge/a2a
	@echo "Cleaned bridge/"

a2a-cards: ## Generate A2A agent cards for cross-framework discovery
	@echo "=== Generating A2A agent cards ==="
	@uv run python scripts/a2a_cards.py --output bridge/a2a/
	@echo "=== A2A cards ready at bridge/a2a/ ==="

a2a-list: ## List agents available for A2A card generation
	@uv run python scripts/a2a_cards.py --list

detect-framework: ## Detect active agentic framework
	@uv run python scripts/framework_detect.py

cross-framework: clawhub-export bridge-build a2a-cards ## Build all cross-framework artifacts
	@echo ""
	@echo "=== Cross-Framework Build Complete ==="
	@echo "  ClawHub export: clawhub/ ($$(find clawhub -name '*.json' 2>/dev/null | wc -l | tr -d ' ') skills)"
	@echo "  OpenClaw bridge: bridge/openclaw/ (plugin ready)"
	@echo "  A2A agent cards: bridge/a2a/ ($$(find bridge/a2a -name '*.json' 2>/dev/null | wc -l | tr -d ' ') agents)"
	@echo ""
	@uv run python scripts/framework_detect.py

verify-deferred-capture:  ## Verify all deferred_capture.py wrappers conform to leyline contract
	@echo "Verifying deferred_capture.py compliance..."
	@for plugin in sanctum attune imbue pensive abstract egregore; do \
		echo "  $$plugin..."; \
		python3 plugins/$$plugin/scripts/deferred_capture.py \
			--title "Test: compliance" \
			--source test \
			--context "Automated compliance check" \
			--dry-run | python3 -c "import json,sys; d=json.load(sys.stdin); assert 'status' in d, 'Missing status field'" \
		|| { echo "  FAIL: $$plugin"; exit 1; }; \
	done
	@echo "All wrappers compliant."

demo: ## Demonstrate Claude Night Market capabilities
	@echo "=== Claude Night Market Demo ==="
	@echo ""
	@echo "Installed Plugins:"
	@for plugin in $(ALL_PLUGINS); do \
		name=$$(basename $$plugin); \
		desc=$$(head -5 $$plugin/.claude-plugin/plugin.json 2>/dev/null | grep '"description"' | cut -d'"' -f4 | head -c 50); \
		echo "  - $$name: $$desc..."; \
	done
	@echo ""
	@echo "Quick Commands:"
	@echo "  make help           - Show all available targets"
	@echo "  make status         - Show plugin status overview"
	@echo "  make plugin-check   - Run all plugin self-tests"
	@echo "  make test           - Run tests across all plugins"
	@echo "  make lint           - Run linting across all plugins"
	@echo ""
	@echo "Per-Plugin Commands:"
	@echo "  make <plugin>-help  - Show plugin-specific targets"
	@echo "  make <plugin>-test  - Run plugin tests"
	@echo ""
	@echo "Example: make abstract-help"
