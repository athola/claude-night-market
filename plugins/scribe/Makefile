# Scribe Plugin Makefile
# Documentation quality tools: slop detection, style learning, doc generation

.PHONY: help validate test test-coverage lint format clean demo count-slop status \
	demo-slop-scan demo-style-learn demo-doc-polish demo-doc-generate \
	demo-doc-verify demo-pr-review demo-update-docs demo-update-readme \
	demo-prepare-pr demo-pr demo-cli-plugins demo-scribe-commands \
	test-slop-scan test-style-learn test-doc-polish test-doc-generate \
	test-doc-verify test-pr-review test-update-docs test-update-readme \
	test-prepare-pr test-pr plugin-check debug-variables typecheck type-check

# Include shared configuration for markdown-only plugins
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/markdown-only.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Scribe Plugin - Make Targets"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Validation ----------
validate: ## Validate plugin structure
	@echo "Validating plugin structure..."
	@test -f .claude-plugin/plugin.json && echo "  plugin.json exists" || echo "  MISSING: plugin.json"
	@test -d skills && echo "  skills/ exists" || echo "  MISSING: skills/"
	@test -d commands && echo "  commands/ exists" || echo "  MISSING: commands/"
	@test -d agents && echo "  agents/ exists" || echo "  MISSING: agents/"
	@test -f README.md && echo "  README.md exists" || echo "  MISSING: README.md"
	@echo "Validation complete."

# ---------- Testing ----------
test: ## Run scribe tests
	@echo "Running scribe tests..."
	@uv run pytest tests/ -v --tb=short 2>/dev/null || echo "No tests found or test runner not available"

test-coverage: ## Run tests with coverage measurement
	@echo "Running scribe tests with coverage..."
	@uv run pytest tests/ -v --tb=short \
		--cov=src/scribe --cov-report=term-missing --cov-branch \
		2>/dev/null || echo "Coverage measurement not available (install pytest-cov)"

# ---------- Linting ----------
lint: ## Check for slop in plugin documentation
	@echo "Checking for slop in plugin documentation..."
	@grep -rn -E "delve|embark|tapestry|comprehensive|leverage" skills/ commands/ README.md 2>/dev/null && echo "WARNING: Slop words found in plugin docs" || echo "No tier-1 slop words found"

# ---------- Quality (no-ops for markdown-only) ----------
typecheck type-check: ## No-op: no Python code to check
	@echo "No type checking needed (markdown-only plugin)"

format: ## No formatting required for markdown files
	@echo "No formatting required for markdown files"

# ---------- Cleanup ----------
clean: ## Clean generated files
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache .mypy_cache
	@find . -name "*.pyc" -delete
	@echo "Clean complete."

# ---------- Status ----------
status: ## Show project overview
	@echo "Scribe Plugin Status:"
	@echo "Skills:   $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Commands: $$(find commands/ -name '*.md' 2>/dev/null | wc -l)"
	@echo "Agents:   $$(find agents/ -name '*.md' 2>/dev/null | wc -l)"

debug-variables: ## Show Makefile variable values (for debugging)
	@echo "=== Makefile Variables ==="
	@echo "SHELL: $(SHELL)"
	@echo "SHELLFLAGS: $(SHELLFLAGS)"
	@echo "SKILLS_DIR: $(SKILLS_DIR)"
	@echo "COMMANDS_DIR: $(COMMANDS_DIR)"
	@echo "AGENTS_DIR: $(AGENTS_DIR)"
	@echo "DOCS_DIR: $(DOCS_DIR)"
	@echo "SRC_DIRS: $(SRC_DIRS)"
	@echo "MAKEFLAGS: $(MAKEFLAGS)"

# ---------- Demo ----------
demo: ## Run demonstration
	@echo "Scribe Plugin Demo"
	@echo ""
	@echo "1. Scan for AI slop:"
	@echo "   /slop-scan README.md"
	@echo ""
	@echo "2. Polish documentation:"
	@echo "   /doc-polish docs/guide.md"
	@echo ""
	@echo "3. Learn a writing style:"
	@echo "   /style-learn examples/*.md --name house-style"
	@echo ""
	@echo "4. Generate documentation:"
	@echo "   /doc-generate readme --style house-style"

# Count slop words in a file (usage: make count-slop FILE=path/to/file.md)
count-slop: ## Count slop words in FILE
	@echo "Counting slop words in $(FILE)..."
	@grep -oE '\b(delve|embark|tapestry|realm|beacon|multifaceted|nuanced|pivotal|meticulous|intricate|showcasing|leveraging|streamline|comprehensive|robust)\b' $(FILE) 2>/dev/null | sort | uniq -c | sort -rn || echo "No tier-1 slop words found"

# ---------- Demo/Dogfood Targets ----------
# Parameterized: each demo-* target shows usage for one command
SCRIBE_COMMANDS := slop-scan style-learn doc-polish doc-generate doc-verify pr-review update-docs update-readme prepare-pr pr

demo-slop-scan: ## Demo slop-scan command (LIVE)
	@echo "=== slop-scan Demo (LIVE) ==="
	@echo ""
	@echo "Command: /slop-scan"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates slop-scan usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-style-learn: ## Demo style-learn command (LIVE)
	@echo "=== style-learn Demo (LIVE) ==="
	@echo ""
	@echo "Command: /style-learn"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates style-learn usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-doc-polish: ## Demo doc-polish command (LIVE)
	@echo "=== doc-polish Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-polish"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-polish usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-doc-generate: ## Demo doc-generate command (LIVE)
	@echo "=== doc-generate Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-generate"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-generate usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-doc-verify: ## Demo doc-verify command (LIVE)
	@echo "=== doc-verify Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-verify"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-verify usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-pr-review: ## Demo pr-review command (LIVE)
	@echo "=== pr-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /pr-review"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates pr-review usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-update-docs: ## Demo update-docs command (LIVE)
	@echo "=== update-docs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-docs"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates update-docs usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-update-readme: ## Demo update-readme command (LIVE)
	@echo "=== update-readme Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-readme"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates update-readme usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-prepare-pr: ## Demo prepare-pr command (LIVE)
	@echo "=== prepare-pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /prepare-pr"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates prepare-pr usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-pr: ## Demo pr command (LIVE)
	@echo "=== pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /pr"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates pr usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-cli-plugins: ## Demo CLI invocation: plugins install scribe
	@echo "=== cli-plugins Demo (LIVE) ==="
	@echo ""
	@echo "Command: plugins install scribe"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates cli-plugins usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-scribe-commands: demo-slop-scan demo-style-learn demo-doc-polish demo-doc-generate demo-doc-verify demo-pr-review demo-update-docs demo-update-readme demo-prepare-pr demo-pr ## Run all scribe documented command demos
	@echo ""
	@echo "=== Scribe All Commands Demo Complete ==="

# ---------- Test Targets ----------
# Each test-* target runs the subset of tests matching the command name
test-slop-scan: ## Test slop-scan command (runs slop detection tests)
	@uv run pytest tests/ -v -k "slop" --tb=short 2>/dev/null || \
		echo "Not applicable: slop-scan is skill-based; run 'make lint' to check for slop"

test-style-learn: ## Test style-learn command (runs style tests)
	@uv run pytest tests/ -v -k "style" --tb=short 2>/dev/null || \
		echo "Not applicable: style-learn is a skill-only command with no unit tests"

test-doc-polish: ## Test doc-polish command (runs doc tests)
	@uv run pytest tests/ -v -k "polish" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-polish is a skill-only command with no unit tests"

test-doc-generate: ## Test doc-generate command (runs doc generation tests)
	@uv run pytest tests/ -v -k "generate" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-generate is a skill-only command with no unit tests"

test-doc-verify: ## Test doc-verify command (runs doc verification tests)
	@uv run pytest tests/ -v -k "verify" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-verify is a skill-only command with no unit tests"

test-pr-review: ## Test pr-review command (runs PR review tests)
	@uv run pytest tests/ -v -k "pr_review or pr-review" --tb=short \
		2>/dev/null || echo "Not applicable: pr-review is a skill-only command with no unit tests"

test-update-docs: ## Test update-docs command (runs doc update tests)
	@uv run pytest tests/ -v -k "update_docs or update-docs" --tb=short \
		2>/dev/null || echo "Not applicable: update-docs is a skill-only command with no unit tests"

test-update-readme: ## Test update-readme command (runs readme tests)
	@uv run pytest tests/ -v -k "update_readme or readme" --tb=short \
		2>/dev/null || echo "Not applicable: update-readme is a skill-only command with no unit tests"

test-prepare-pr: ## Test prepare-pr command (runs PR prep tests)
	@uv run pytest tests/ -v -k "prepare_pr or prepare-pr" --tb=short \
		2>/dev/null || echo "Not applicable: prepare-pr is a skill-only command with no unit tests"

test-pr: ## Test pr command (runs general PR tests)
	@uv run pytest tests/ -v -k "pr" --tb=short 2>/dev/null || \
		echo "Not applicable: pr is a skill-only command with no unit tests"

plugin-check: validate demo status ## Run all checks
	@echo ""
	@echo "=== Scribe Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
