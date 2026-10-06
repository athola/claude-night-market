# Scribe Plugin Makefile
# Documentation quality tools: slop detection, style learning, doc generation

.PHONY: help validate test test-coverage lint format clean demo count-slop status \
	demo-cli-plugins demo-scribe-commands \
	test-doc-generate test-doc-polish test-session-replay test-session-to-post \
	test-style-learn test-voice-extract test-voice-generate test-voice-learn \
	test-voice-review plugin-check debug-variables typecheck type-check

# Include shared configuration for markdown-only plugins
ABSTRACT_DIR := ../abstract
include $(ABSTRACT_DIR)/config/make/markdown-only.mk

# ---------- Help ----------
help: ## Show this help message
	@echo "Scribe Plugin - Make Targets"
	@echo "============================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------- Validation ----------
validate: ## Validate plugin structure
	@echo "Validating plugin structure..."
	@fail=0; \
	for path in .claude-plugin/plugin.json README.md; do \
		if [ -f "$$path" ]; then echo "  $${path##*/} exists"; \
		else echo "  MISSING: $${path##*/}"; fail=1; fi; \
	done; \
	for dir in skills commands agents; do \
		if [ -d "$$dir" ]; then echo "  $$dir/ exists"; \
		else echo "  MISSING: $$dir/"; fail=1; fi; \
	done; \
	echo "Validation complete."; exit $$fail

# ---------- Testing ----------
test: ## Run scribe tests
	@echo "Running scribe tests..."
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v --tb=short

test-coverage: ## Run tests with coverage measurement
	@echo "Running scribe tests with coverage..."
	@cd ../.. && uv run pytest plugins/scribe/tests/ -v --tb=short \
		--cov=plugins/scribe/src/scribe --cov-report=term-missing --cov-branch

# ---------- Linting ----------
lint: ## Ratchet plugin docs against the repo slop scorer (fails on regression)
	@echo "Scoring plugin documentation for slop..."
	@cd ../.. && uv run --with pyyaml python scripts/slop_score.py --threshold 3.0 --ratchet HEAD plugins/scribe/skills plugins/scribe/commands plugins/scribe/README.md

# ---------- Quality ----------
typecheck type-check: ## Type-check src/scribe with mypy
	@uv run python -m mypy src/scribe

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
	@echo "Commands: $$(find commands/ -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)"
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
	@test -f "$(FILE)" || { echo "Usage: make count-slop FILE=path/to/file.md (no such file: '$(FILE)')"; exit 1; }
	@echo "Counting slop words in $(FILE)..."
	@hits=$$(grep -oE '\b(delve|embark|tapestry|realm|beacon|multifaceted|nuanced|pivotal|meticulous|intricate|showcasing|leveraging|streamline|comprehensive|robust)\b' "$(FILE)") || [ $$? -eq 1 ]; \
	if [ -z "$$hits" ]; then echo "No tier-1 slop words found"; \
	else printf '%s\n' "$$hits" | sort | uniq -c | sort -rn; fi

# ---------- Demo/Dogfood Targets ----------
# One demo per commands/*.md, so the list cannot drift from what ships.
SCRIBE_COMMANDS := $(sort $(basename $(notdir $(wildcard commands/*.md))))
SCRIBE_DEMOS := $(addprefix demo-,$(SCRIBE_COMMANDS))
.PHONY: $(SCRIBE_DEMOS)

$(SCRIBE_DEMOS): demo-%:
	@echo "=== $* Demo ==="
	@echo ""
	@echo "Command: /$*"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates $* usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-cli-plugins: ## Demo CLI invocation: plugins install scribe
	@echo "=== cli-plugins Demo (informational) ==="
	@echo ""
	@echo "Command: plugins install scribe"
	@echo "Plugin: scribe"
	@echo ""
	@echo "This demonstrates cli-plugins usage."
	@echo "Execute manually in Claude Code for full functionality."

demo-scribe-commands: $(SCRIBE_DEMOS) ## Run all scribe documented command demos
	@echo ""
	@echo "=== Scribe All Commands Demo Complete ==="

# ---------- Test Targets ----------
# Each test-* target runs the subset of tests matching the command name.
#
# The subset may legitimately be empty: several scribe commands are
# skill-only and ship no unit tests. Reporting that as "not applicable"
# is correct. Reporting a *failing* run that way is finding F-C from the
# 2026-06-28 dogfooding pass, and it is what `pytest ... || echo` does,
# because `||` cannot tell the two apart.
#
# pytest can: exit code 5 means "no tests collected". Branch on it and
# re-raise every other status, so an empty subset skips and a broken test
# fails. Guarded by tests/unit/test_plugin_check_harness.py.
#
# `|| status=$$?` rather than `; status=$$?` because this Makefile
# inherits `.SHELLFLAGS := -euo pipefail -c`. Under errexit a bare
# `;` aborts the shell the moment pytest returns non-zero, so the
# capture never runs; consuming the status with `||` marks the
# failure handled.
#
# --no-cov because a -k subset is not a coverage measurement. With
# the project threshold applied, every subset run failed the 85% gate
# on its own narrowness, which is the pressure that produced the
# `|| echo` mask in the first place.
define run_test_subset
@status=0; \
	cd ../.. && uv run pytest plugins/scribe/tests/ -v -k "$(1)" \
		--tb=short --no-cov || status=$$?; \
	if [ "$$status" -eq 5 ]; then \
		echo "Not applicable: no scribe test matches '$(1)'"; \
	else \
		exit "$$status"; \
	fi
endef

test-style-learn: ## Test style-learn command (runs style tests)
	$(call run_test_subset,style)

test-doc-polish: ## Test doc-polish command (runs doc tests)
	$(call run_test_subset,polish)

test-doc-generate: ## Test doc-generate command (runs doc generation tests)
	$(call run_test_subset,generate)

test-session-replay: ## Test session-replay command (runs session parser and tape tests)
	$(call run_test_subset,session or tape or codex)

test-session-to-post: ## Test session-to-post command
	$(call run_test_subset,session_to_post or session-to-post)

test-voice-extract: ## Test voice-extract command
	$(call run_test_subset,voice_extract or voice-extract)

test-voice-generate: ## Test voice-generate command
	$(call run_test_subset,voice_generate or voice-generate)

test-voice-learn: ## Test voice-learn command
	$(call run_test_subset,voice_learn or voice-learn)

test-voice-review: ## Test voice-review command
	$(call run_test_subset,voice_review or voice-review)

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
