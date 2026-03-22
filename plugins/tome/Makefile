# Tome Plugin Makefile
# Multi-source research: code archaeology, discourse, academic, TRIZ
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help deps test test-unit test-coverage lint format type-check typecheck \
	security clean ci status debug-variables fix \
	demo-classify demo-plan demo-skills demo-channels plugin-check \
	test-channels test-synthesis test-output \
	mutation-test benchmark memory-profile

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests
RUFF_TARGETS := src/ tests/
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
COV_DIRS := src/tome
PYTEST_TARGETS := tests/
TEST_UNIT_TARGETS := tests/unit/
TEST_UNIT_ARGS := -v --tb=short
COV_REPORTS := --cov-report=html --cov-report=term-missing

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Tome Plugin - Make Targets"
	@echo "=========================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Dependencies ----------
deps: ## Install and sync dependencies
	$(UV) sync

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

test-channels: ## Run channel-specific tests
	$(PYTEST) tests/channels/ -v --tb=short

test-synthesis: ## Run synthesis tests (merger, ranker)
	$(PYTEST) tests/unit/ -v -k "merger or ranker" --tb=short

test-output: ## Run output tests (export, visualizer)
	$(PYTEST) tests/output/ -v --tb=short

# ---------- Code Quality ----------
fix: ## Auto-fix lint issues
	$(RUFF) check --fix $(RUFF_TARGETS)

ci: lint type-check test ## Run CI pipeline
	@echo "CI pipeline completed!"

# ---------- Maintenance ----------
clean: ## Clean build artifacts
	rm -rf .pytest_cache htmlcov .coverage .mypy_cache .ruff_cache 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Tome Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Source:   $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"
	@echo "Tests:    $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "PYTHON: $(PYTHON)"
	@echo "UV: $(UV)"
	@echo "UV_RUN: $(UV_RUN)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "RUFF_TARGETS: $(RUFF_TARGETS)"
	@echo "MYPY_TARGETS: $(MYPY_TARGETS)"
	@echo "BANDIT_TARGETS: $(BANDIT_TARGETS)"
	@echo "COV_DIRS: $(COV_DIRS)"
	@echo "PYTEST_TARGETS: $(PYTEST_TARGETS)"

# ---------- Advanced Testing ----------
mutation-test: ## Run mutation testing
	@if command -v mutmut >/dev/null 2>&1; then \
		mutmut run --paths-to-mutate src/tome --tests-dir tests/; \
	else \
		echo "mutmut not installed (pip install mutmut)"; \
	fi

benchmark: ## Run performance benchmarks
	$(PYTEST) --benchmark-only --benchmark-sort=mean || echo "pytest-benchmark not installed"

memory-profile: ## Profile memory usage
	@if python3 -c "import memory_profiler" 2>/dev/null; then \
		$(UV_RUN) python3 -m memory_profiler src/tome/scripts/*.py; \
	else \
		echo "Install memory_profiler: pip install memory_profiler"; \
	fi

# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-classify: ## Demo domain classifier on sample topics (LIVE)
	@echo "=== Tome Domain Classifier Demo (LIVE) ==="
	@echo ""
	$(UV_RUN) python -c "\
	from tome.scripts.domain_classifier import classify; \
	topics = ['react component design patterns', 'rust memory safety', 'kubernetes deployment']; \
	[print(f'  {t}: domain={classify(t).domain}, triz={classify(t).triz_depth}, confidence={classify(t).confidence:.2f}') for t in topics]"
	@echo ""
	@echo "Use /tome:research for full research workflow."

demo-plan: ## Demo research planner on classified topic (LIVE)
	@echo "=== Tome Research Planner Demo (LIVE) ==="
	@echo ""
	$(UV_RUN) python -c "\
	from tome.scripts.domain_classifier import classify; \
	from tome.scripts.research_planner import plan; \
	c = classify('distributed systems consensus algorithms'); \
	p = plan(c); \
	print(f'  Topic: distributed systems consensus algorithms'); \
	print(f'  Domain: {c.domain} (confidence: {c.confidence:.2f})'); \
	print(f'  Channels: {p.channels}'); \
	print(f'  Budget: {p.estimated_budget} tokens'); \
	print(f'  TRIZ depth: {c.triz_depth}')"
	@echo ""
	@echo "Use /tome:dig for deep research."

demo-channels: ## Show available research channels
	@echo "=== Tome Research Channels ==="
	@echo ""
	@echo "Channel modules:"
	@for ch in src/tome/channels/*.py; do \
		name=$$(basename "$$ch" .py); \
		[ "$$name" = "__init__" ] && continue; \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Agents:"
	@for agent in agents/*.md; do \
		name=$$(basename "$$agent" .md); \
		echo "  - $$name"; \
	done

demo-skills: ## Validate tome skill structure
	@echo "=== Tome Skills Demo ==="
	@echo "Research skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done 2>/dev/null || echo "  (no skills found)"

plugin-check: demo-classify demo-plan demo-channels demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Tome Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
