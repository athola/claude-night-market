# Archetypes Plugin Makefile
# Architecture paradigm patterns and templates (markdown-only plugin)
#
# This is a minimal Makefile for a markdown-only plugin

.PHONY: help status clean demo-paradigms demo-skills plugin-check debug-variables

# Include shared configuration for markdown-only plugins
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/markdown-only.mk

# Default target
help: ## Show this help message
	@echo "Archetypes Plugin - Make Targets"
	@echo "================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Note: This is a markdown-only plugin (no Python code)"

# ---------- Info ----------
status: ## Show project overview
	@echo "Archetypes Plugin Status:"
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Total markdown: $$(find . -name '*.md' 2>/dev/null | wc -l) files"

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

# ---------- Maintenance ----------
clean: ## Clean any generated files
	@echo "Nothing to clean (markdown-only plugin)"

# ---------- Demo/Dogfood Targets ----------
demo-paradigms: ## List available architecture paradigms
	@echo "=== Archetypes Paradigms Demo ==="
	@echo "Available architecture paradigms:"
	@echo ""
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		desc=$$(head -15 "$$skill" | grep '^description:' | cut -d: -f2- | head -c 60); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Total paradigms: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"

demo-skills: ## Validate archetypes skill structure
	@echo "=== Archetypes Skills Demo ==="
	@echo "Checking skill frontmatter..."
	@echo ""
	@for skill in skills/*/SKILL.md; do \
		name=$$(basename $$(dirname $$skill)); \
		has_name=$$(grep -c '^name:' "$$skill" 2>/dev/null || echo 0); \
		has_desc=$$(grep -c '^description:' "$$skill" 2>/dev/null || echo 0); \
		if [ "$$has_name" -gt 0 ] && [ "$$has_desc" -gt 0 ]; then \
			echo "  [OK] $$name"; \
		else \
			echo "  [X] $$name (missing frontmatter)"; \
		fi; \
	done
	@echo ""
	@echo "Skills validation complete."

plugin-check: demo-paradigms demo-skills status ## Run all demo workflows
	@echo ""
	@echo "=== Archetypes Plugin Check Complete ==="

# Include local overrides if they exist (before catch-all rule)
Makefile.local:;
-include Makefile.local

# Guard against accidental file creation (catch-all for unknown targets)
%::
	@echo "Error: Unknown target '$@'"
	@echo "Run 'make help' to see available commands"
	@exit 1
