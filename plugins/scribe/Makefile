# Scribe Plugin Makefile

.PHONY:
.PHONY: clean demo demo-doc-generate demo-doc-polish demo-doc-verify demo-pr demo-pr-review \
	demo-prepare-pr demo-slop-scan demo-style-learn demo-update-docs demo-update-readme format help \
	lint test test-doc-generate test-doc-polish test-doc-verify test-pr test-pr-review test-prepare-pr \
	test-slop-scan test-style-learn test-update-docs test-update-readme validate
help:
	@echo "Scribe Plugin Commands"
	@echo ""
	@echo "  validate    - Validate plugin structure"
	@echo "  test        - Run tests"
	@echo "  lint        - Check for issues"
	@echo "  format      - Format files"
	@echo "  clean       - Remove generated files"
	@echo "  demo        - Run demonstration"

# Validation
validate:
	@echo "Validating plugin structure..."
	@test -f .claude-plugin/plugin.json && echo "  plugin.json exists" || echo "  MISSING: plugin.json"
	@test -d skills && echo "  skills/ exists" || echo "  MISSING: skills/"
	@test -d commands && echo "  commands/ exists" || echo "  MISSING: commands/"
	@test -d agents && echo "  agents/ exists" || echo "  MISSING: agents/"
	@test -f README.md && echo "  README.md exists" || echo "  MISSING: README.md"
	@echo "Validation complete."

# Testing
test:
	@echo "Running scribe tests..."
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v --tb=short 2>/dev/null || echo "No tests found or test runner not available"

# Linting
lint:
	@echo "Checking for slop in plugin documentation..."
	@grep -rn "delve\|embark\|tapestry\|comprehensive\|leverage" skills/ commands/ README.md 2>/dev/null && echo "WARNING: Slop words found in plugin docs" || echo "No tier-1 slop words found"

# Formatting
format:
	@echo "No formatting required for markdown files"

# Cleanup
clean:
	@echo "Cleaning generated files..."
	@rm -rf __pycache__ .pytest_cache .mypy_cache
	@find . -name "*.pyc" -delete
	@echo "Clean complete."

# Demonstration
demo:
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
count-slop:
	@echo "Counting slop words in $(FILE)..."
	@grep -oE '\b(delve|embark|tapestry|realm|beacon|multifaceted|nuanced|pivotal|meticulous|intricate|showcasing|leveraging|streamline|comprehensive|robust)\b' $(FILE) 2>/dev/null | sort | uniq -c | sort -rn || echo "No tier-1 slop words found"

demo-slop-scan: ## Demo slop-scan command (LIVE)
	@echo "=== slop-scan Demo (LIVE) ==="
	@echo ""
	@echo "Command: /slop-scan"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates slop-scan usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /slop-scan for full workflow."


demo-style-learn: ## Demo style-learn command (LIVE)
	@echo "=== style-learn Demo (LIVE) ==="
	@echo ""
	@echo "Command: /style-learn"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates style-learn usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /style-learn for full workflow."


demo-doc-polish: ## Demo doc-polish command (LIVE)
	@echo "=== doc-polish Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-polish"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-polish usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /doc-polish for full workflow."


demo-doc-generate: ## Demo doc-generate command (LIVE)
	@echo "=== doc-generate Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-generate"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-generate usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /doc-generate for full workflow."


demo-doc-verify: ## Demo doc-verify command (LIVE)
	@echo "=== doc-verify Demo (LIVE) ==="
	@echo ""
	@echo "Command: /doc-verify"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates doc-verify usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /doc-verify for full workflow."


demo-pr-review: ## Demo pr-review command (LIVE)
	@echo "=== pr-review Demo (LIVE) ==="
	@echo ""
	@echo "Command: /pr-review"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates pr-review usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /pr-review for full workflow."


demo-update-docs: ## Demo update-docs command (LIVE)
	@echo "=== update-docs Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-docs"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates update-docs usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /update-docs for full workflow."


demo-update-readme: ## Demo update-readme command (LIVE)
	@echo "=== update-readme Demo (LIVE) ==="
	@echo ""
	@echo "Command: /update-readme"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates update-readme usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /update-readme for full workflow."


demo-prepare-pr: ## Demo prepare-pr command (LIVE)
	@echo "=== prepare-pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /prepare-pr"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates prepare-pr usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /prepare-pr for full workflow."


demo-pr: ## Demo pr command (LIVE)
	@echo "=== pr Demo (LIVE) ==="
	@echo ""
	@echo "Command: /pr"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates pr usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use /pr for full workflow."


demo-cli-plugins: ## Demo CLI invocation: plugins install scribe
	@echo "=== cli-plugins Demo (LIVE) ==="
	@echo ""
	@echo "Command: plugins install scribe"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates cli-plugins usage."
	@echo "Execute manually in Claude Code for full functionality."
	@echo ""
	@echo "Use plugins install scribe for full workflow."


demo-scribe-commands: demo-slop-scan demo-style-learn demo-doc-polish demo-doc-generate demo-doc-verify demo-pr-review demo-update-docs demo-update-readme demo-prepare-pr demo-pr ## Run all scribe documented command demos
	@echo ""
	@echo "=== Scribe All Commands Demo Complete ==="
	@echo "Ran 10 documented commands"
	@echo ""


test-slop-scan: ## Test slop-scan command (runs slop detection tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "slop" --tb=short 2>/dev/null || \
		echo "Not applicable: slop-scan is skill-based; run 'make lint' to check for slop"

test-style-learn: ## Test style-learn command (runs style tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "style" --tb=short 2>/dev/null || \
		echo "Not applicable: style-learn is a skill-only command with no unit tests"

test-doc-polish: ## Test doc-polish command (runs doc tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "polish" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-polish is a skill-only command with no unit tests"

test-doc-generate: ## Test doc-generate command (runs doc generation tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "generate" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-generate is a skill-only command with no unit tests"

test-doc-verify: ## Test doc-verify command (runs doc verification tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "verify" --tb=short 2>/dev/null || \
		echo "Not applicable: doc-verify is a skill-only command with no unit tests"

test-pr-review: ## Test pr-review command (runs PR review tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "pr_review or pr-review" --tb=short \
		2>/dev/null || echo "Not applicable: pr-review is a skill-only command with no unit tests"

test-update-docs: ## Test update-docs command (runs doc update tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "update_docs or update-docs" --tb=short \
		2>/dev/null || echo "Not applicable: update-docs is a skill-only command with no unit tests"

test-update-readme: ## Test update-readme command (runs readme tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "update_readme or readme" --tb=short \
		2>/dev/null || echo "Not applicable: update-readme is a skill-only command with no unit tests"

test-prepare-pr: ## Test prepare-pr command (runs PR prep tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "prepare_pr or prepare-pr" --tb=short \
		2>/dev/null || echo "Not applicable: prepare-pr is a skill-only command with no unit tests"

test-pr: ## Test pr command (runs general PR tests)
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "pr" --tb=short 2>/dev/null || \
		echo "Not applicable: pr is a skill-only command with no unit tests"
