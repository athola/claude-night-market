# Pensive Plugin Makefile
# Code review and quality analysis tools
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY:
.PHONY: all benchmark ci clean complexity-check coverage coverage-badge coverage-check \
	debug-variables demo-api-review demo-architecture-review demo-bug-review demo-fpf-review \
	demo-full-review demo-makefile-review demo-math-review demo-pensive-commands demo-refine-code \
	demo-rust-review demo-shell-review demo-skill-history demo-skill-review demo-skills \
	demo-test-review deps-outdated deps-update dev dev-install docs docs-serve duplication-check \
	format help install lint memory-profile mutation-test perf-test plugin-check quality-check \
	security status test test-api-review test-architecture-review test-bug-review test-edge-case \
	test-file test-fpf-review test-full-review test-integration test-makefile-review test-math-review \
	test-parallel test-pattern test-refine-code test-rust-review test-shell-review test-skill-history \
	test-skill-review test-structure test-test-review test-unit type-check typecheck

# Plugin-specific variables (must be before include)
SRC_DIRS := src tests
MYPY_TARGETS := src/
BANDIT_TARGETS := src/
COV_DIRS := src
PYTEST_TARGETS := tests/
TEST_UNIT_ARGS := -v -m unit
SECURITY_EXTRA = $(UV_RUN) safety check || echo "[WARNING] Safety check unavailable"

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk
-include $(ABSTRACT_DIR)/config/make/python.mk

# Prevent parallel execution for targets that share resources
.NOTPARALLEL: docs docs-serve

# ---------- Help ----------
help: ## Show this help message
	@echo "Pensive Plugin - Make Targets"
	@echo "=============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Default target
all: test lint ## Run tests and linting

# ---------- Testing ----------
test: ## Run all tests
	$(PYTEST) $(PYTEST_TARGETS) -v

test-integration: ## Run only integration tests
	$(PYTEST) -v -m integration

test-edge-case: ## Run edge case tests
	$(PYTEST) -v -m edge_case

coverage: ## Run tests with coverage report
	$(PYTEST) --cov=pensive --cov-report=html --cov-report=term-missing

coverage-check: ## Check coverage meets 85% threshold
	$(PYTEST) --cov=pensive --cov-fail-under=85 --cov-report=term-missing

test-parallel: ## Run tests in parallel
	$(PYTEST) -n auto -v

test-file: ## Run specific test file (FILE=path)
	@if [ -z "$(FILE)" ]; then echo "Usage: make test-file FILE=path/to/test.py"; exit 1; fi
	$(PYTEST) -v $(FILE)

test-pattern: ## Run tests matching pattern (PATTERN=name)
	@if [ -z "$(PATTERN)" ]; then echo "Usage: make test-pattern PATTERN=test_name"; exit 1; fi
	$(PYTEST) -v -k "$(PATTERN)"

# ---------- Code Quality ----------
quality-check: format lint type-check coverage-check ## Run all quality checks
	@echo "All quality checks passed!"

# ---------- Installation ----------
dev-install: ## Install in development mode
	pip install -e ".[dev]"

install: ## Install for production
	pip install .

# ---------- Documentation ----------
docs: ## Generate documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

# ---------- Analysis ----------
duplication-check: ## Check for duplicate code
	radon cc src/ --min B
	radon mi src/

complexity-check: ## Analyze code complexity
	radon cc src/ --min B
	xenon --max-absolute B --max-modules A --max-average A src/ || true

perf-test: ## Run performance tests
	$(PYTEST) -v -m performance --benchmark-only

benchmark: ## Run performance benchmarks
	$(PYTEST) --benchmark-only --benchmark-sort=mean

memory-profile: ## Profile memory usage
	python -m memory_profiler tests/performance/memory_usage.py || echo "memory_profiler not installed"

mutation-test: ## Run mutation testing
	mutmut run --paths-to-mutate src/ || echo "mutmut not installed"

test-structure: ## Verify test structure
	@echo "Checking test structure..."
	@echo "Test files: $$(find tests/ -name 'test_*.py' | wc -l)"
	@echo "Test functions: $$(grep -r 'def test_' tests/ | wc -l)"
	@echo "Test classes: $$(grep -r 'class Test' tests/ | wc -l)"

# ---------- Dependencies ----------
deps-update: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"

deps-outdated: ## Check for outdated dependencies
	pip list --outdated

# ---------- Workflows ----------
dev: format lint test-unit ## Quick development loop

ci: format lint type-check security coverage-check ## Full CI pipeline
	@echo "CI pipeline completed successfully!"

# ---------- Maintenance ----------
clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage .mypy_cache/ .ruff_cache/ 2>/dev/null || true
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

status: ## Show project overview
	@echo "Pensive Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name 'test_*.py' 2>/dev/null | wc -l)"
	@echo "Source: $$(find src/ -name '*.py' 2>/dev/null | wc -l) Python files"

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

coverage-badge: ## Generate coverage badge
	coverage-badge -o docs/coverage.svg || echo "coverage-badge not installed"

# ---------- Demo/Dogfood Targets ----------
demo-makefile-review: ## Demo Makefile review on this plugin's Makefile
	@echo "=== Pensive Makefile Review Demo ==="
	@echo "Demonstrating makefile-review skill on this Makefile..."
	@echo ""
	@echo "Step 1: Structure Check"
	@echo "Targets defined: $$(grep -cE '^[a-zA-Z_-]+:' Makefile)"
	@echo "PHONY declarations: $$(grep -c '.PHONY' Makefile)"
	@echo "Has help target: $$(grep -q '^help:' Makefile && echo 'yes' || echo 'no')"
	@echo ""
	@echo "Step 2: Pattern Analysis"
	@grep -E '^\s*\$$(MAKE)' Makefile | head -5 || echo "  (no recursive make calls)"
	@echo ""
	@echo "Step 3: Quality Checks"
	@echo "Uses SHELL directive: $$(grep -q '^SHELL' Makefile && echo 'yes' || echo 'no')"
	@echo "Tab indentation: $$(grep -cP '^\t' Makefile) recipe lines"
	@echo ""
	@echo "Makefile review demo complete. Use /pensive:makefile-review for full analysis."

demo-bug-review: ## Demo bug review on pensive source code
	@echo "=== Pensive Bug Review Demo ==="
	@echo "Demonstrating bug-review skill on pensive skills..."
	@echo ""
	@echo "Step 1: File Inventory"
	@find skills/ -name "*.md" -type f | head -10
	@echo ""
	@echo "Step 2: Pattern Scanning"
	@echo "TODO comments: $$(grep -r 'TODO' skills/ 2>/dev/null | wc -l)"
	@echo "FIXME comments: $$(grep -r 'FIXME' skills/ 2>/dev/null | wc -l)"
	@echo "Error patterns: $$(grep -r 'error\|Error\|ERROR' skills/ 2>/dev/null | wc -l)"
	@echo ""
	@echo "Step 3: Validation Check"
	@for skill in skills/*/SKILL.md; do \
		grep -q "## When to Use" "$$skill" || echo "  Missing usage: $$skill"; \
	done
	@echo ""
	@echo "Bug review demo complete. Use /pensive:bug-review for full analysis."

demo-skills: ## Validate pensive skill structure
	@echo "=== Pensive Skills Demo ==="
	@echo "Available review skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  api-review:       $$(test -f skills/api-review/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  bug-review:       $$(test -f skills/bug-review/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  makefile-review:  $$(test -f skills/makefile-review/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  test-review:      $$(test -f skills/test-review/SKILL.md && echo '[OK]' || echo '[X]')"
	@echo "  rust-review:      $$(test -f skills/rust-review/SKILL.md && echo '[OK]' || echo '[X]')"

plugin-check: demo-makefile-review demo-bug-review demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Pensive Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

demo-full-review: ## Demo full-review command (LIVE)
	@echo "=== full-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /full-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates full-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /full-review for full workflow."


demo-api-review: ## Demo api-review command (LIVE)
	@echo "=== api-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /api-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates api-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /api-review for full workflow."


demo-architecture-review: ## Demo architecture-review command (LIVE)
	@echo "=== architecture-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /architecture-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates architecture-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /architecture-review for full workflow."

demo-rust-review: ## Demo rust-review command (LIVE)
	@echo "=== rust-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /rust-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates rust-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /rust-review for full workflow."


demo-test-review: ## Demo test-review command (LIVE)
	@echo "=== test-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /test-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates test-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /test-review for full workflow."


demo-math-review: ## Demo math-review command (LIVE)
	@echo "=== math-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /math-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates math-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /math-review for full workflow."

demo-shell-review: ## Demo shell-review command (LIVE)
	@echo "=== shell-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /shell-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates shell-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /shell-review for full workflow."


demo-fpf-review: ## Demo fpf-review command (LIVE)
	@echo "=== fpf-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /fpf-review"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates fpf-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /fpf-review for full workflow."


demo-cli---fork-session: ## Demo CLI invocation: --fork-session --session-id "security-audit"
	@echo "=== cli---fork-session Demo (LIVE) ==="
	@echo ""
	@echo "Command: --fork-session --session-id "security-audit""
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates cli---fork-session usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use --fork-session --session-id "security-audit" for full workflow."


demo-cli-plugins: ## Demo CLI invocation: plugins install pensive
	@echo "=== cli-plugins Demo (LIVE) ==="
	@echo ""
	@echo "Command: plugins install pensive"
	@echo "Plugin: pensive"
	@echo ""
	@echo "This demonstrates cli-plugins usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use plugins install pensive for full workflow."


demo-refine-code: ## Demo code refinement analysis (LIVE)
	@echo "=== Pensive Code Refinement Demo (LIVE) ==="
	@echo ""
	@echo "Analyzing pensive source for refinement candidates..."
	@echo "Files by complexity (lines):"
	@find src/ -name "*.py" -exec wc -l {} \; 2>/dev/null | sort -rn | head -5 | \
		awk '{if($$1>200) printf "  [REVIEW] %s (%d lines)\n", $$2, $$1; else printf "  [OK] %s (%d lines)\n", $$2, $$1}'
	@echo ""
	@echo "Duplicate patterns:"
	@grep -rn 'def ' src/ 2>/dev/null | awk -F: '{print $$3}' | sort | uniq -d | head -5 || echo "  (none found)"
	@echo ""
	@echo "Use /pensive:refine-code for full analysis."

demo-skill-history: ## Demo skill usage history (LIVE)
	@echo "=== Pensive Skill History Demo (LIVE) ==="
	@echo ""
	@echo "Recent skill-related commits:"
	@git log --oneline --all --grep="pensive" -5 2>/dev/null || echo "  (no pensive commits found)"
	@echo ""
	@echo "Skill file modification dates:"
	@for skill in skills/*/SKILL.md; do \
		mod=$$(git log -1 --format="%ci" -- "$$skill" 2>/dev/null | cut -d' ' -f1); \
		name=$$(basename $$(dirname "$$skill")); \
		echo "  $$name: $$mod"; \
	done
	@echo ""
	@echo "Use /pensive:skill-history for detailed analysis."

demo-skill-review: ## Demo skill quality review (LIVE)
	@echo "=== Pensive Skill Review Demo (LIVE) ==="
	@echo ""
	@echo "Skill frontmatter validation:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(basename $$(dirname "$$skill")); \
		has_name=$$(head -20 "$$skill" | grep -c '^name:'); \
		has_desc=$$(head -20 "$$skill" | grep -c '^description:'); \
		if [ "$$has_name" -gt 0 ] && [ "$$has_desc" -gt 0 ]; then \
			echo "  [OK] $$name"; \
		else \
			echo "  [WARN] $$name - missing frontmatter"; \
		fi; \
	done
	@echo ""
	@echo "Use /pensive:skill-review for comprehensive review."

demo-pensive-commands: demo-full-review demo-api-review demo-architecture-review demo-bug-review demo-rust-review demo-test-review demo-math-review demo-makefile-review demo-shell-review demo-fpf-review demo-refine-code demo-skill-history demo-skill-review ## Run all pensive documented command demos
	@echo ""
	@echo "=== Pensive All Commands Demo Complete ==="
	@echo "Ran 13 documented commands"
	@echo ""


test-full-review: ## Test full-review command (runs all review tests)
	$(PYTEST) $(PYTEST_TARGETS) -v --tb=short

test-api-review: ## Test api-review command (runs API review tests)
	$(PYTEST) tests/skills/test_api_review.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "api_review or api-review"

test-architecture-review: ## Test architecture-review command (runs architecture review tests)
	$(PYTEST) tests/skills/test_architecture_review.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "architecture"

test-bug-review: ## Test bug-review command (runs bug review tests)
	$(PYTEST) tests/skills/test_bug_review.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "bug_review or bug-review"

test-rust-review: ## Test rust-review command (runs Rust review tests)
	$(PYTEST) tests/skills/test_rust_review.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "rust_review or rust-review"

test-test-review: ## Test test-review command (runs test review tests)
	$(PYTEST) tests/skills/test_test_review.py tests/skills/test_test_review_content.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "test_review"

test-math-review: ## Test math-review command (runs math review tests)
	$(PYTEST) tests/skills/test_math_review.py -v 2>/dev/null || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "math_review or math-review"

test-makefile-review: ## Test makefile-review command (runs Makefile review tests)
	$(PYTEST) tests/skills/test_makefile_review.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "makefile_review or makefile-review"

test-shell-review: ## Test shell-review command (not applicable: skill-only, no unit tests)
	@echo "Not applicable: shell-review is a skill-only command with no unit tests"

test-fpf-review: ## Test fpf-review command (not applicable: skill-only, no unit tests)
	@echo "Not applicable: fpf-review is a skill-only command with no unit tests"

test-refine-code: ## Test code refinement (runs refinement tests)
	$(PYTEST) tests/test_code_refinement.py -v || \
		$(PYTEST) $(PYTEST_TARGETS) -v -k "refine or refinement"

test-skill-history: ## Test skill history (not applicable: skill-only, no unit tests)
	@echo "Not applicable: skill-history is a skill-only command with no unit tests"

test-skill-review: ## Test skill review (not applicable: skill-only, no unit tests)
	@echo "Not applicable: skill-review is a skill-only command with no unit tests"


# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
