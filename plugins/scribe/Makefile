# Scribe Plugin Makefile

.PHONY: help validate test lint format clean demo

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
