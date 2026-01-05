# Scry Plugin Makefile
# Media generation capabilities for terminal and browser recordings
#
# Uses shared Make includes from abstract plugin for DRY compliance

.PHONY: help validate status clean check-deps lint test test-unit test-integration demo-vhs demo-playwright demo-gif clean-gif-temp demo-skills plugin-check debug-variables ci-check

# Plugin-specific variables (must be before include)
SRC_DIRS := scripts

# Include shared configuration from abstract plugin
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/markdown-only.mk

GIF_DEMO_DIR ?= /tmp/scry-gif-test
TMP_DIR ?= $(GIF_DEMO_DIR)
GIF_DEMO_SCRIPT := $(SCRIPTS_DIR)/gif-demo.sh

# Default target - auto-generated help from ## comments
help: ## Show this help message
	@echo "Scry Plugin - Make Targets"
	@echo "==========================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' Makefile

# ---------- Validation ----------
validate: ## Validate plugin structure and dependencies
	@echo "Validating scry plugin structure..."
	@test -f .claude-plugin/plugin.json && echo "  [OK] plugin.json exists" || echo "  [X] plugin.json missing"
	@test -d skills/vhs-recording && echo "  [OK] vhs-recording skill dir exists" || echo "  [X] vhs-recording missing"
	@test -d skills/browser-recording && echo "  [OK] browser-recording skill dir exists" || echo "  [X] browser-recording missing"
	@test -d skills/gif-generation && echo "  [OK] gif-generation skill dir exists" || echo "  [X] gif-generation missing"
	@test -d skills/media-composition && echo "  [OK] media-composition skill dir exists" || echo "  [X] media-composition missing"
	@test -d commands && echo "  [OK] commands dir exists" || echo "  [X] commands missing"
	@echo "Validation complete."

check-deps: ## Check if required dependencies are installed
	@echo "Checking scry dependencies..."
	@command -v vhs >/dev/null 2>&1 && echo "  [OK] vhs installed: $$(vhs --version 2>/dev/null || echo 'unknown')" || echo "  [X] vhs not installed (brew install charmbracelet/tap/vhs)"
	@command -v ffmpeg >/dev/null 2>&1 && echo "  [OK] ffmpeg installed: $$(ffmpeg -version 2>&1 | head -1)" || echo "  [X] ffmpeg not installed"
	@command -v npx >/dev/null 2>&1 && echo "  [OK] npx available" || echo "  [X] npx not installed (install Node.js)"
	@npx playwright --version >/dev/null 2>&1 && echo "  [OK] playwright installed" || echo "  [!] playwright not installed (npx playwright install)"
	@echo "Dependency check complete."

# ---------- Status ----------
status: ## Show project overview
	@echo "Scry Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Tapes:    $$(find . -name '*.tape' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(SHELLFLAGS)"
	@echo "SKILLS_DIR: $(SKILLS_DIR)"
	@echo "COMMANDS_DIR: $(COMMANDS_DIR)"
	@echo "AGENTS_DIR: $(AGENTS_DIR)"
	@echo "DOCS_DIR: $(DOCS_DIR)"
	@echo "SCRIPTS_DIR: $(SCRIPTS_DIR)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"

# ---------- Quality Gates ----------
lint: ## Lint scry shell scripts (bash -n)
	@echo "=== Scry Lint ==="
	@if ls $(SCRIPTS_DIR)/*.sh >/dev/null 2>&1; then \
		for file in $(SCRIPTS_DIR)/*.sh; do \
			bash -n "$$file"; \
		done; \
		echo "  [OK] bash -n"; \
	else \
		echo "  [SKIP] no shell scripts"; \
	fi
	@echo "=== Lint Complete ==="

typecheck: ## Run type checking on test files
	@echo "=== Scry Type Checking ==="
	@if command -v uv >/dev/null 2>&1; then \
		uv run mypy tests/ --strict; \
	else \
		echo "  [SKIP] uv not installed"; \
	fi
	@echo "=== Type Checking Complete ==="

test: test-unit ## Run all scry tests

test-unit: ## Run unit tests (no external dependencies)
	@echo "=== Scry Unit Tests ==="
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v -m "not integration" --tb=short; \
	elif command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ -v -m "not integration" --tb=short; \
	else \
		echo "  [SKIP] pytest not installed"; \
	fi
	@echo "=== Unit Tests Complete ==="

test-integration: ## Run integration tests (requires ffmpeg/vhs)
	@echo "=== Scry Integration Tests ==="
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ -v -m "integration" --tb=short; \
	elif command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ -v -m "integration" --tb=short; \
	else \
		echo "  [SKIP] pytest not installed"; \
	fi
	@if command -v ffmpeg >/dev/null 2>&1; then \
		$(MAKE) demo-gif; \
		$(MAKE) clean-gif-temp; \
	else \
		echo "  [SKIP] ffmpeg not installed"; \
	fi
	@echo "=== Integration Tests Complete ==="

ci-check: lint test-unit ## Run all CI checks locally
	@echo "=== Scry CI Check Complete ==="

# ---------- Demo/Dogfood Targets ----------
demo-vhs: ## Demo VHS recording workflow
	@echo "=== Scry VHS Demo ==="
	@echo "Demonstrating VHS terminal recording workflow..."
	@echo ""
	@echo "Step 1: Check VHS availability"
	@command -v vhs >/dev/null 2>&1 && echo "  VHS is installed" || echo "  VHS not found - install with: brew install charmbracelet/tap/vhs"
	@echo ""
	@echo "Step 2: Example tape script"
	@echo "  Output demo.gif"
	@echo "  Set FontSize 16"
	@echo "  Set Width 1200"
	@echo "  Set Height 600"
	@echo "  Type \"echo 'Hello, World!'\""
	@echo "  Sleep 500ms"
	@echo "  Enter"
	@echo "  Sleep 2s"
	@echo ""
	@echo "Step 3: Run with: vhs example.tape"
	@echo ""
	@echo "VHS demo complete. Use /record-terminal for full workflow."

demo-playwright: ## Demo Playwright browser recording workflow
	@echo "=== Scry Playwright Demo ==="
	@echo "Demonstrating Playwright browser recording workflow..."
	@echo ""
	@echo "Step 1: Check Playwright availability"
	@npx playwright --version >/dev/null 2>&1 && echo "  Playwright is installed" || echo "  Playwright not found - install with: npx playwright install"
	@echo ""
	@echo "Step 2: Recording commands"
	@echo "  npx playwright codegen https://example.com"
	@echo "  npx playwright screenshot https://example.com screenshot.png"
	@echo ""
	@echo "Step 3: For video recording, use Playwright test runner with video option"
	@echo ""
	@echo "Playwright demo complete. Use /record-browser for full workflow."

demo-gif: ## Generate a demo GIF in temp paths
	@echo "=== Scry GIF Demo ==="
	@TMP_DIR="$(TMP_DIR)" "$(GIF_DEMO_SCRIPT)"
	@echo "=== GIF Demo Complete ==="

clean-gif-temp: ## Remove temp GIF demo files
	@echo "Cleaning temp GIF demo files..."
	@rm -rf "$(TMP_DIR)"
	@echo "Cleanup completed."

demo-skills: ## Validate scry skill and agent structure
	@echo "=== Scry Skills Demo ==="
	@echo "Media generation skills:"
	@for dir in skills/*/; do \
		name=$$(basename "$$dir"); \
		if [ -f "$$dir/SKILL.md" ]; then \
			echo "  - $$name [OK]"; \
		else \
			echo "  - $$name [pending]"; \
		fi; \
	done
	@echo ""
	@echo "Skill coverage:"
	@echo "  vhs-recording:      $$(test -f skills/vhs-recording/SKILL.md && echo '[OK]' || echo '[pending]')"
	@echo "  browser-recording:  $$(test -f skills/browser-recording/SKILL.md && echo '[OK]' || echo '[pending]')"
	@echo "  gif-generation:     $$(test -f skills/gif-generation/SKILL.md && echo '[OK]' || echo '[pending]')"
	@echo "  media-composition:  $$(test -f skills/media-composition/SKILL.md && echo '[OK]' || echo '[pending]')"
	@echo ""
	@echo "Agent coverage:"
	@echo "  media-recorder:     $$(test -f agents/media-recorder.md && echo '[OK]' || echo '[pending]')"

plugin-check: validate check-deps demo-vhs demo-playwright demo-skills ## Run all demo workflows
	@echo ""
	@echo "=== Scry Plugin Check Complete ==="

# ---------- Cleanup ----------
clean: ## Clean up generated files
	@echo "Cleaning up..."
	rm -rf *.gif *.mp4 *.webm 2>/dev/null || true
	rm -rf recordings/ output/ 2>/dev/null || true
	@echo "Cleanup completed!"

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
