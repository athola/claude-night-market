# Claude Night Market - Root Makefile
# Delegates to plugin Makefiles for build operations

.PHONY: help all test lint typecheck clean status validate-all plugin-check check-examples \
        docs docs-fast demo \
        technical-debt-scan technical-debt-dashboard technical-debt-plan technical-debt-kpis \
        technical-debt-setup technical-debt-integration \
        abstract abstract-% conjure conjure-% conservation conservation-% \
        imbue imbue-% memory-palace memory-palace-% parseltongue parseltongue-% \
        pensive pensive-% sanctum sanctum-% spec-kit spec-kit-%

# Default shell with error handling
SHELL := /bin/bash
.SHELLFLAGS := -euo pipefail -c

# Local tool cache (avoids permission issues with default locations)
UV_TOOL_DIR ?= $(abspath .)/.uv-tools
PATH := $(UV_TOOL_DIR)/ruff/bin:$(PATH)

# Plugin directories
PLUGINS_DIR := plugins
ABSTRACT_DIR := $(PLUGINS_DIR)/abstract
CONJURE_DIR := $(PLUGINS_DIR)/conjure
CONSERVATION_DIR := $(PLUGINS_DIR)/conservation
IMBUE_DIR := $(PLUGINS_DIR)/imbue
MEMORY_PALACE_DIR := $(PLUGINS_DIR)/memory-palace
PARSELTONGUE_DIR := $(PLUGINS_DIR)/parseltongue
PENSIVE_DIR := $(PLUGINS_DIR)/pensive
SANCTUM_DIR := $(PLUGINS_DIR)/sanctum
SPEC_KIT_DIR := $(PLUGINS_DIR)/spec-kit
ARCHETYPES_DIR := $(PLUGINS_DIR)/archetypes
LEYLINE_DIR := $(PLUGINS_DIR)/leyline
SHARED_DIR := $(PLUGINS_DIR)/shared
MINISTER_DIR := $(PLUGINS_DIR)/minister

# All plugin directories for iteration (auto-detected)
PLUGIN_MAKEFILES := $(wildcard $(PLUGINS_DIR)/*/Makefile)
ALL_PLUGINS := $(patsubst %/Makefile,%,$(PLUGIN_MAKEFILES))

# Default target
all: lint test ## Run lint and test across all plugins

help: ## Show this help message
	@echo ""
	@echo "Claude Night Market - Make Targets"
	@echo "==================================="
	@echo ""
	@echo "Root targets:"
	@echo "  help              Show this help message"
	@echo "  all               Run lint and test across all plugins"
	@echo "  test              Run tests in all plugins"
	@echo "  lint              Run linting in all plugins"
	@echo "  typecheck         Run type checking in all plugins"
	@echo "  docs              Build marketplace docs via Quill wrapper"
	@echo "  docs-fast         Quick plugin-only docs build (set PLUGIN=name)"
	@echo "  status            Show status of all plugins"
	@echo "  clean             Clean all plugin artifacts"
	@echo "  validate-all      Validate all plugin structures"
	@echo "  plugin-check      Run demo/dogfood checks across all plugins"
	@echo "  check-examples    Verify all plugins have proper examples"
	@echo ""
	@echo "Technical Debt Framework:"
	@echo "  technical-debt-setup      Install technical debt framework dependencies"
	@echo "  technical-debt-scan       Run detailed technical debt scan"
	@echo "  technical-debt-dashboard  Generate debt dashboard and reports"
	@echo "  technical-debt-plan       Generate quarterly sprint plan"
	@echo "  technical-debt-kpis       Calculate current KPIs and metrics"
	@echo "  technical-debt-integration Setup integrations with external tools"
	@echo ""
	@echo "Plugin delegation (run with 'make <plugin>-<target>'):"
	@echo "  abstract-*        Abstract plugin targets (e.g., abstract-test)"
	@echo "  conjure-*         Conjure plugin targets"
	@echo "  conservation-*    Conservation plugin targets"
	@echo "  imbue-*           Imbue plugin targets"
	@echo "  memory-palace-*   Memory Palace plugin targets"
	@echo "  parseltongue-*    Parseltongue plugin targets"
	@echo "  pensive-*         Pensive plugin targets"
	@echo "  sanctum-*         Sanctum plugin targets"
	@echo "  spec-kit-*        Spec-Kit plugin targets"
	@echo ""
	@echo "Examples:"
	@echo "  make abstract-help      Show abstract plugin targets"
	@echo "  make pensive-test       Run pensive tests"
	@echo "  make sanctum-lint       Run sanctum linting"
	@echo "  make technical-debt-scan Run technical debt scan"
	@echo ""
	@echo "Or use 'make -C <plugin-dir> <target>' directly"

# Technical Debt Framework Targets
technical-debt-setup: ## Install technical debt framework dependencies
	@echo "Setting up Technical Debt Framework..."
	pip install matplotlib psutil requests PyGithub
	@echo "Technical Debt Framework dependencies installed"

technical-debt-scan: ## Run detailed technical debt scan
	@echo "Running technical debt scan..."
	python scripts/enhanced_technical_debt_detector.py . --output json > debt_scan_results.json
	@echo "Creating workflows from debt data..."
	python scripts/technical_debt_workflow_manager.py . create-workflows > /dev/null 2>&1 || true
	@echo "Technical debt scan completed. Results saved to debt_scan_results.json"

technical-debt-dashboard: ## Generate debt dashboard and visualizations
	@echo "Generating technical debt dashboard..."
	mkdir -p debt_reports
	python scripts/debt_dashboard_generator.py . --output-dir debt_reports
	@echo "Dashboard generated: debt_reports/technical_debt_dashboard.html"
	@echo "Opening dashboard in browser..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open debt_reports/technical_debt_dashboard.html; \
	elif command -v open > /dev/null; then \
		open debt_reports/technical_debt_dashboard.html; \
	else \
		echo "Dashboard available at: debt_reports/technical_debt_dashboard.html"; \
	fi

technical-debt-plan: ## Generate quarterly sprint plan
	@echo "Generating quarterly technical debt sprint plan..."
	python scripts/quarterly_debt_sprint_planner.py . --output-dir sprint_plans
	@echo "Sprint plan generated: sprint_plans/"
	@echo "Latest plan: sprint_plans/latest_sprint_plan.md"

technical-debt-kpis: ## Calculate current KPIs and metrics
	@echo "Calculating technical debt KPIs..."
	python scripts/technical_debt_metrics_kpi.py . kpis > current_kpis.json
	@echo "KPIs calculated. Results saved to current_kpis.json"
	@echo "Current health score:"
	@python -c "import json; data=json.load(open('current_kpis.json')); health = data.get('debt_health_score', {}).get('value', 'N/A'); print(f'  Health Score: {health}')"

technical-debt-integration: ## Setup integrations with external tools
	@echo "Setting up technical debt integrations..."
	@echo "Generating JIRA export..."
	python scripts/technical_debt_integration.py . generate-jira-export
	@echo "Generating TeamCity configuration..."
	python scripts/technical_debt_integration.py . teamcity-integration
	@echo "Integration files generated in current directory"

technical-debt-report: ## Generate detailed technical debt report
	@echo "Generating detailed technical debt report..."
	mkdir -p reports
	python scripts/technical_debt_metrics_kpi.py . report 90 > reports/quarterly_debt_report.json
	python scripts/debt_dashboard_generator.py . --output-dir reports
	@echo "detailed report generated in reports/ directory"

technical-debt-clean: ## Clean technical debt artifacts and data
	@echo "Cleaning technical debt artifacts..."
	rm -f debt_scan_results.json
	rm -f current_kpis.json
	rm -f jira_technical_debt_export.json
	rm -f teamcity_technical_debt.json
	rm -rf debt_reports/
	rm -rf sprint_plans/
	rm -rf reports/
	@echo "Technical debt artifacts cleaned"

# Aggregate targets
test: ## Run tests in all plugins
	@echo "=== Running Tests Across All Plugins ==="
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo ""; \
			echo ">>> Testing $$plugin"; \
			$(MAKE) -C $$plugin test 2>/dev/null || echo "  (test failed or unavailable)"; \
		fi; \
	done
	@echo ""
	@echo "=== Test Run Complete ==="

lint: ## Run linting in all plugins
	@echo "=== Running Lint Across All Plugins ==="
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo ""; \
			echo ">>> Linting $$plugin"; \
			$(MAKE) -C $$plugin lint 2>/dev/null || echo "  (lint failed or unavailable)"; \
		fi; \
	done
	@echo ""
	@echo "=== Lint Complete ==="

typecheck: ## Run type checking in all plugins
	@echo "=== Running Type Checks Across All Plugins ==="
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo ""; \
			echo ">>> Type checking $$plugin"; \
			export PYTHONPATH="$(abspath .):${PYTHONPATH}:"; \
			$(MAKE) -C $$plugin typecheck 2>/dev/null || echo "  (typecheck failed or unavailable)"; \
		fi; \
	done
	@echo ""
	@echo "=== Type Check Complete ==="

# Plugin delegation - Abstract
abstract-%:
	@$(MAKE) -C $(ABSTRACT_DIR) $*

abstract:
	@$(MAKE) -C $(ABSTRACT_DIR)

# Plugin delegation - Conjure
conjure-%:
	@$(MAKE) -C $(CONJURE_DIR) $*

conjure:
	@$(MAKE) -C $(CONJURE_DIR)

# Plugin delegation - Conservation
conservation-%:
	@$(MAKE) -C $(CONSERVATION_DIR) $*

conservation:
	@$(MAKE) -C $(CONSERVATION_DIR)

# Plugin delegation - Imbue
imbue-%:
	@$(MAKE) -C $(IMBUE_DIR) $*

imbue:
	@$(MAKE) -C $(IMBUE_DIR)

# Plugin delegation - Memory Palace
memory-palace-%:
	@$(MAKE) -C $(MEMORY_PALACE_DIR) $*

memory-palace:
	@$(MAKE) -C $(MEMORY_PALACE_DIR)

# Plugin delegation - Parseltongue
parseltongue-%:
	@$(MAKE) -C $(PARSELTONGUE_DIR) $*

parseltongue:
	@$(MAKE) -C $(PARSELTONGUE_DIR)

# Plugin delegation - Pensive
pensive-%:
	@$(MAKE) -C $(PENSIVE_DIR) $*

pensive:
	@$(MAKE) -C $(PENSIVE_DIR)

# Plugin delegation - Sanctum
sanctum-%:
	@$(MAKE) -C $(SANCTUM_DIR) $*

sanctum:
	@$(MAKE) -C $(SANCTUM_DIR)

# Plugin delegation - Spec-Kit
spec-kit-%:
	@$(MAKE) -C $(SPEC_KIT_DIR) $*

spec-kit:
	@$(MAKE) -C $(SPEC_KIT_DIR)

status: ## Show status of all plugins
	@echo "=== Plugin Status ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> $$plugin:"; \
		$(MAKE) -C $$plugin status 2>/dev/null || echo "  (status unavailable)"; \
	done
	@echo ""
	@echo "=== Technical Debt Framework Status ==="
	@if [ -f "current_kpis.json" ]; then \
		echo "[OK] Technical debt tracking is active"; \
		python -c "import json; data=json.load(open('current_kpis.json')); health = data.get('debt_health_score', {}).get('value', 'N/A'); echo f'   Health Score: {health}'"; \
	else \
		echo "[TODO] Technical debt tracking not initialized (run 'make technical-debt-scan')"; \
	fi
	@if [ -d "debt_reports" ]; then \
		echo "[OK] Dashboard available at: debt_reports/technical_debt_dashboard.html"; \
	fi

clean: ## Clean all plugin artifacts and technical debt data
	@echo "Cleaning all plugins..."
	@for plugin in $(ALL_PLUGINS); do \
		if [ -f "$$plugin/Makefile" ]; then \
			echo "Cleaning $$plugin..."; \
			$(MAKE) -C $$plugin clean 2>/dev/null || true; \
		fi; \
	done
	@echo "Cleaning technical debt artifacts..."
	$(MAKE) technical-debt-clean
	@echo "Done."

validate-all: ## Validate all plugin structures
	@echo "=== Validating Plugin Structures ==="
	@for plugin in $(ALL_PLUGINS); do \
		echo ""; \
		echo ">>> Validating $$plugin:"; \
		python3 $(ABSTRACT_DIR)/scripts/validate-plugin.py $$plugin || echo "  (validation failed)"; \
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

docs: ## Build marketplace docs (uses scripts/build-marketplace-docs.sh)
	@./scripts/build-marketplace-docs.sh

docs-fast: ## Build docs for a single plugin without marketplace (PLUGIN=name, default abstract)
	@./scripts/build-marketplace-docs.sh --plugin $(or $(PLUGIN),abstract) --no-marketplace

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
	@echo "New in v1.1.2 - Bloat Detection:"
	@echo "  make conservation-demo-bloat  - Demo bloat detection on conservation plugin"
	@echo "  /bloat-scan --level 2         - Run bloat scan in Claude Code"
	@echo "  /unbloat --from-scan report   - Safe bloat remediation"
	@echo ""
	@echo "Example: make abstract-help"
