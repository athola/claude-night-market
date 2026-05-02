# Gauntlet Plugin Makefile
# Codebase learning through knowledge extraction and spaced repetition

.PHONY: help deps fix check clean \
	status debug-variables \
	lint format type-check typecheck security test-unit test \
	demo-gauntlet demo-gauntlet-extract demo-gauntlet-curate \
	demo-gauntlet-graph demo-gauntlet-progress demo-gauntlet-onboard \
	demo-all \
	test-gauntlet test-gauntlet-extract test-gauntlet-curate \
	test-gauntlet-graph test-gauntlet-progress test-gauntlet-onboard

# Plugin-specific variables (must be before include)
SRC_DIRS := src/gauntlet scripts hooks tests
RUFF_TARGETS := src/gauntlet/ tests/
MYPY_TARGETS := src/gauntlet/
BANDIT_TARGETS := src/gauntlet/
COV_DIRS := src/gauntlet
PYTEST_TARGETS := tests/

ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Note: lint, format, type-check, typecheck, security, test-unit,
# test-coverage, test-quick are provided by python.mk

help: ## Show this help message
	@echo "Gauntlet Plugin - Make Targets"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

deps: ## Install dependencies
	$(UV) sync

fix: ## Auto-fix lint issues
	$(RUFF) check --fix $(RUFF_TARGETS)

test: ## Run tests
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

check: lint type-check test ## Run all checks
	@echo "All checks passed!"

clean: ## Clean artifacts
	rm -rf .venv .uv-cache __pycache__ .mypy_cache .pytest_cache

status: ## Show project overview
	@echo "Gauntlet Plugin Status:"
	@echo "Source:   $$(find src/gauntlet/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"

# ---------------------------------------------------------------------------
# LIVE demo targets — dogfood gauntlet's own scripts on its own codebase.
# These run actual functionality and produce real output, not static echoes.
# ---------------------------------------------------------------------------

demo-gauntlet-extract: ## Demo: extract knowledge entries from gauntlet's own source (LIVE)
	@echo "=== gauntlet-extract Demo: dogfood on src/gauntlet/ (LIVE) ==="
	@$(UV_RUN) python scripts/extractor.py src/gauntlet --format text | head -20
	@echo "..."
	@echo "(truncated to 20 entries; remove '| head' for full output)"

demo-gauntlet-curate: ## Demo: read-only survey of the bundled problem bank (LIVE)
	@echo "=== gauntlet-curate Demo: read-only problem-bank survey (LIVE) ==="
	@$(UV_RUN) python scripts/curate_problems.py --verbose 2>&1 | head -30 || true

demo-gauntlet-graph: ## Demo: show graph_query CLI surface and supported actions (LIVE)
	@echo "=== gauntlet-graph Demo: graph_query CLI surface (LIVE) ==="
	@$(UV_RUN) python scripts/graph_query.py --help

demo-gauntlet-progress: ## Demo: show progress_tracker CLI surface (LIVE)
	@echo "=== gauntlet-progress Demo: progress_tracker CLI surface (LIVE) ==="
	@$(UV_RUN) python scripts/progress_tracker.py --help

demo-gauntlet: ## Demo: show challenge_engine CLI surface (LIVE)
	@echo "=== gauntlet Demo: challenge_engine CLI surface (LIVE) ==="
	@$(UV_RUN) python scripts/challenge_engine.py --help

demo-gauntlet-onboard: ## Demo: print the onboard skill's actual workflow steps (LIVE)
	@echo "=== gauntlet-onboard Demo: skill workflow excerpt (LIVE) ==="
	@head -40 skills/onboard/SKILL.md

demo-all: demo-gauntlet demo-gauntlet-extract demo-gauntlet-curate \
          demo-gauntlet-graph demo-gauntlet-progress \
          demo-gauntlet-onboard ## Run every demo target in sequence
	@echo "=== demo-all complete ==="

# ---------------------------------------------------------------------------
# Per-command test targets — scope pytest to the surface each command exercises.
# ---------------------------------------------------------------------------

# Per-command test targets use --no-cov: they exercise a slice of the
# plugin, not the full surface, so the 85% global threshold doesn't apply.
# Use `make test` (or test-coverage) for the full-suite coverage gate.

test-gauntlet: ## Run tests covering challenge generation + CLI scripts
	$(PYTEST) tests/unit/test_challenges.py tests/unit/test_cli_scripts.py -v --tb=short --no-cov

test-gauntlet-extract: ## Run tests covering knowledge extraction
	$(PYTEST) tests/unit/test_extraction.py -v --tb=short --no-cov

test-gauntlet-curate: ## Run tests covering problem-bank curation
	$(PYTEST) tests/unit/test_curate_problems.py tests/unit/test_problem_bank.py -v --tb=short --no-cov

test-gauntlet-graph: ## Run tests covering the code knowledge graph
	$(PYTEST) tests/unit/test_graph.py tests/unit/test_graph_auto_update.py \
		tests/unit/test_graph_challenges.py tests/unit/test_communities.py \
		tests/unit/test_incremental.py -v --tb=short --no-cov

test-gauntlet-progress: ## Run tests covering progress tracking
	$(PYTEST) tests/unit/test_progress.py -v --tb=short --no-cov

test-gauntlet-onboard: ## Run tests covering onboarding flow logic
	$(PYTEST) tests/unit/test_flows.py -v --tb=short --no-cov

Makefile.local:;
-include Makefile.local

%::
	@echo "Error: Unknown target '$$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
