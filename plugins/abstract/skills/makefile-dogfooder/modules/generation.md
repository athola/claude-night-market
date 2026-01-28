# Target Generation Module

## Overview

This module provides templates and workflows for generating contextually appropriate Makefile targets for plugins in the claude-night-market project. It supports both aggregator and leaf plugin patterns with customizable templates.

## Core Principle: LIVE Demonstrations

**CRITICAL:** Demo targets must run ACTUAL functionality, not just echo static information.

| ❌ BAD (Static/Informational) | ✅ GOOD (Live/Functional) |
|-------------------------------|---------------------------|
| `@echo "Skills: 5"` | `@$(UV_RUN) python scripts/validator.py --scan` |
| `@find skills/ -name '*.md' \| wc -l` | `@$(UV_RUN) python scripts/cli.py analyze skills/` |
| `@echo "Feature: token estimation"` | `@$(UV_RUN) python scripts/token_estimator.py --file README.md` |

**Reference Pattern** (from ragentop):
```makefile
demo-detection: build  ## Demonstrate agent session detection (LIVE)
	@echo "=== Agent Session Detection Demo (LIVE) ==="
	@./target/release/ragentop detect --verbose
```

This runs the actual tool and shows REAL output that users would see.

## Template Categories

### 1. Demo Targets

**Purpose:** Demonstrate plugin functionality by RUNNING actual user-facing tools

#### Live Demo Template (Preferred)
```makefile
demo-$(FEATURE): ## Demonstrate $(FEATURE) functionality (LIVE)
	@echo "=== $(PLUGIN_NAME) $(FEATURE) Demo (LIVE) ==="
	@echo ""
	$(UV_RUN) python scripts/$(FEATURE_SCRIPT).py $(DEMO_ARGS)
	@echo ""
	@echo "Use /$(PLUGIN_NAME):$(SKILL_NAME) for full workflow."
```

#### Self-Dogfooding Demo Template
```makefile
demo-dogfood: ## Run plugin tools on this plugin (LIVE)
	@echo "=== $(PLUGIN_NAME) Self-Dogfood Demo (LIVE) ==="
	@echo "Running $(TOOL_NAME) on $(PLUGIN_NAME) plugin itself..."
	@echo ""
	$(UV_RUN) python scripts/$(TOOL_NAME).py --target . $(TOOL_ARGS)
```

#### Fallback Demo Template (when no CLI exists)
```makefile
demo: ## Run plugin demonstration
	@echo "=== $(PLUGIN_NAME) Demo ==="
	@echo ""
	@echo "Available skills (invoke with /$(PLUGIN_NAME):<skill>):"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		desc=$$(head -10 "$$skill" | grep '^description:' | cut -d: -f2- | head -c 60); \
		echo "  - $$name: $$desc"; \
	done
	@echo ""
	@echo "No CLI tools available. Use slash commands for functionality."
```

### 2. Dogfood Targets

**Purpose:** Test the plugin on itself using its own functionality - LIVE execution

#### Live Self-Validation Template (Preferred)
```makefile
plugin-check: ## Run plugin self-validation (LIVE)
	@echo "=== $(PLUGIN_NAME) Self-Check (LIVE) ==="
	@echo ""
	@echo "Running validator on this plugin..."
	$(UV_RUN) python scripts/$(VALIDATOR_SCRIPT).py --target . --report
	@echo ""
	@echo "Plugin validation complete."
```

#### Composite Dogfood Template
```makefile
plugin-check: demo-$(FEATURE1) demo-$(FEATURE2) ## Run all live demos
	@echo ""
	@echo "=== $(PLUGIN_NAME) Plugin Check Complete ==="
```

#### Fallback Self-Test Template (minimal tooling)
```makefile
plugin-test: ## Test plugin using its own tools
	@echo "=== $(PLUGIN_NAME) Self-Test ==="
	@if [ -f scripts/$(PLUGIN_CLI).py ]; then \
		echo "Running CLI self-test..."; \
		$(UV_RUN) python scripts/$(PLUGIN_CLI).py --help; \
		$(UV_RUN) python scripts/$(PLUGIN_CLI).py --test 2>/dev/null || echo "  (no --test flag)"; \
	else \
		echo "No CLI available - running pytest instead..."; \
		$(PYTEST) tests/ -v --tb=short -q; \
	fi
```

### 3. Quick-Run Targets

**Purpose:** Provide fast access to common workflows

#### Status Quick-Run Template
```makefile
quick-status: ## Quick project status
	@echo "$(PLUGIN_NAME): $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l) skills, $$(find scripts/ -name '*.py' 2>/dev/null | wc -l) tools"
```

#### Validate Quick-Run Template
```makefile
quick-validate: ## Quick validation check
	@echo "Validating $(PLUGIN_NAME)..."
	@test -f pyproject.toml || { echo "MISSING pyproject.toml"; exit 1; }
	@test -d skills/ || { echo "MISSING skills/ directory"; exit 1; }
	@echo "OK - Basic structure valid"
```

## Plugin Type Patterns

### Leaf Plugin Templates

**Use Case:** Self-contained plugins with specific functionality

#### Leaf Plugin Base Template
```makefile
# Leaf Plugin: $(PLUGIN_NAME)
# Description: $(PLUGIN_DESCRIPTION)

.PHONY: help all test lint format clean install-hooks \
        status validate-all \
        demo demo-features plugin-check plugin-test \
        quick-status quick-validate

# Include shared configuration
ABSTRACT_DIR := ../abstract
-include $(ABSTRACT_DIR)/config/make/common.mk

# Plugin variables
SRC_DIRS ?= scripts src
PLUGIN_NAME := $(shell basename $(CURDIR))

# Default target
help: ## Show this help message
	@echo "$(PLUGIN_NAME) Plugin - Make Targets"
	@echo "================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Core targets (insert based on available includes)

# Demo/Dogfood targets
demo: ## Run plugin demonstration
	@echo "=== $(PLUGIN_NAME) Demo ==="
	$(DEMO_COMMANDS)

demo-features: ## Demonstrate plugin features
	@echo "=== $(PLUGIN_NAME) Features ==="
	$(FEATURE_COMMANDS)

plugin-check: ## Validate plugin structure
	@echo "=== $(PLUGIN_NAME) Validation ==="
	$(VALIDATION_COMMANDS)

plugin-test: ## Test plugin functionality
	@echo "=== $(PLUGIN_NAME) Test ==="
	$(TEST_COMMANDS)

# Quick-run targets
quick-status: ## Quick status check
	@echo "$(PLUGIN_NAME): $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l) skills"

quick-validate: ## Quick validation
	@test -f pyproject.toml && echo "OK - $(PLUGIN_NAME) structure valid"
```

### Aggregator Plugin Templates

**Use Case:** Root Makefiles that delegate to sub-plugins

#### Aggregator Base Template
```makefile
# Aggregator Plugin: $(PLUGIN_NAME)
# Coordinates: $(SUB_PLUGINS)

.PHONY: help test clean status \
        demo-all check-all \
        plugin-%

# Plugin configuration
SUB_PLUGINS := $(subst /,, $(dir $(wildcard */Makefile)))
PLUGIN_NAME := $(shell basename $(CURDIR))

help: ## Show this help message
	@echo "$(PLUGIN_NAME) - Plugin Aggregator"
	@echo "================================="
	@echo ""
	@echo "Sub-plugins:"
	@for plugin in $(SUB_PLUGINS); do \
		echo "  $$plugin"; \
	done
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / && !/^plugin-/ {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Delegation targets
plugin-%:
	@if [ -d "$*" ] && [ -f "$*/Makefile" ]; then \
		$(MAKE) -C "$*" $(subst plugin-,,$@); \
	else \
		echo "Plugin '$*' not found"; \
		exit 1; \
	fi

# Aggregated targets
test: ## Run tests across all plugins
	@for plugin in $(SUB_PLUGINS); do \
		echo "Testing $$plugin..."; \
		$(MAKE) -C "$$plugin" test 2>/dev/null || echo "  (test failed)"; \
	done

clean: ## Clean all plugins
	@for plugin in $(SUB_PLUGINS); do \
		$(MAKE) -C "$$plugin" clean 2>/dev/null || true; \
	done

status: ## Status of all plugins
	@echo "$(PLUGIN_NAME) Status:"
	@for plugin in $(SUB_PLUGINS); do \
		echo "  $$plugin: $$(find $$plugin/skills/ -name 'SKILL.md' 2>/dev/null | wc -l) skills"; \
	done

# Demo targets
demo-all: ## Demo all plugins
	@for plugin in $(SUB_PLUGINS); do \
		echo "=== $$plugin Demo ==="; \
		$(MAKE) -C "$$plugin" demo 2>/dev/null || echo "  (demo failed)"; \
		echo ""; \
	done

check-all: ## Check all plugins
	@for plugin in $(SUB_PLUGINS); do \
		echo "=== $$plugin Check ==="; \
		$(MAKE) -C "$$plugin" plugin-check 2>/dev/null || echo "  (check failed)"; \
		echo ""; \
	done
```

## Template Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PLUGIN_NAME` | Plugin identifier | `conserve` |
| `PLUGIN_DESCRIPTION` | Brief plugin purpose | `Context optimization and resource management` |
| `PLUGIN_CLI` | Main CLI script name | `conserve-cli` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SRC_DIRS` | Source directories | `scripts src` |
| `FEATURE_1_DESC` | Feature description | `Token usage optimization` |
| `FEATURE_2_DESC` | Feature description | `Context management` |
| `FEATURE_3_DESC` | Feature description | `Performance monitoring` |
| `DEMO_COMMANDS` | Custom demo commands | Generated template |
| `FEATURE_COMMANDS` | Feature demo commands | Generated template |
| `VALIDATION_COMMANDS` | Validation commands | Generated template |
| `TEST_COMMANDS` | Test commands | Generated template |

## Interactive Generation Workflow

### Step 1: Plugin Analysis

```python
def analyze_plugin_for_generation(plugin_dir: str) -> PluginContext:
    """Analyze plugin structure to determine appropriate templates"""
    context = PluginContext()

    # Detect plugin type
    if has_subdirectory_makefiles(plugin_dir):
        context.type = "aggregator"
        context.sub_plugins = find_sub_plugins(plugin_dir)
    else:
        context.type = "leaf"

    # Analyze skills for feature extraction
    skills = find_skills(plugin_dir)
    context.skill_count = len(skills)
    context.feature_descriptions = extract_features_from_skills(skills)

    # Check for existing patterns
    context.has_cli = check_for_cli(plugin_dir)
    context.has_tests = check_for_tests(plugin_dir)
    context.has_docs = check_for_docs(plugin_dir)

    return context
```

### Step 2: Template Selection

```python
def select_templates(context: PluginContext) -> List[str]:
    """Select appropriate templates based on plugin analysis"""
    templates = []

    # Always include basic demo and validation
    templates.append("demo-basic")
    templates.append("plugin-check")

    # Add feature-specific templates
    if context.skill_count > 2:
        templates.append("demo-features")

    if context.has_cli:
        templates.append("plugin-test")

    # Add aggregator-specific templates
    if context.type == "aggregator":
        templates.extend(["demo-all", "check-all"])

    # Add quick-run templates for larger plugins
    if context.skill_count > 5:
        templates.extend(["quick-status", "quick-validate"])

    return templates
```

### Step 3: Customization Prompting

```python
def prompt_customizations(context: PluginContext, templates: List[str]) -> Customization:
    """Prompt user for template customizations"""
    customization = Customization()

    # Feature descriptions
    if "demo-features" in templates and not context.feature_descriptions:
        print("Enter up to 3 feature descriptions for demo:")
        for i in range(3):
            desc = input(f"Feature {i+1} (or press Enter to skip): ").strip()
            if desc:
                customization.features.append(desc)

    # CLI script name
    if context.has_cli and not context.cli_name:
        cli_name = input("Enter CLI script name (without .py): ").strip()
        if cli_name:
            customization.cli_name = cli_name

    # Additional commands
    if "demo" in templates:
        print("Enter any additional demo commands (one per line, empty to finish):")
        while True:
            cmd = input("  > ").strip()
            if not cmd:
                break
            customization.demo_commands.append(cmd)

    return customization
```

### Step 4: Template Generation

```python
def generate_makefile_targets(context: PluginContext,
                            templates: List[str],
                            customization: Customization) -> str:
    """Generate complete Makefile target section"""
    output = []

    output.append(f"\n# ---------- Demo/Dogfood Targets ----------\n")

    # Generate selected templates
    for template in templates:
        rendered = render_template(template, context, customization)
        output.append(rendered)

    # Generate PHONY declaration
    phony_targets = extract_phony_targets(templates)
    output.append(f"\n.PHONY: {' '.join(phony_targets)}\n")

    return "\n".join(output)
```

## Code Examples

### Example 1: Abstract Plugin - LIVE Skill Validation

```makefile
# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-validation: ## Demonstrate plugin validation (LIVE)
	@echo "=== Abstract Validation Demo (LIVE) ==="
	@echo ""
	@echo "Running validator on abstract plugin itself..."
	$(UV_RUN) python scripts/validate_plugin.py .
	@echo ""
	@echo "Use /abstract:validate-plugin for full validation workflow."

demo-tokens: ## Demonstrate token estimation (LIVE)
	@echo "=== Abstract Token Estimation Demo (LIVE) ==="
	@echo ""
	@echo "Estimating tokens for skill-authoring skill..."
	$(UV_RUN) python scripts/token_estimator.py --file skills/skill-authoring/SKILL.md
	@echo ""
	@echo "Use /abstract:estimate-tokens for full estimation workflow."

demo-audit: ## Demonstrate skill auditing (LIVE)
	@echo "=== Abstract Skill Audit Demo (LIVE) ==="
	@echo ""
	@echo "Auditing skills in this plugin..."
	$(UV_RUN) python -c "from abstract.skills_eval import SkillsAuditor; from pathlib import Path; a = SkillsAuditor(Path('.')); r = a.audit_skills(); print(f'Score: {r.get(\"average_score\", 0):.1f}/100')"

plugin-check: demo-validation demo-tokens demo-audit ## Run all live demos
	@echo ""
	@echo "=== Abstract Plugin Check Complete ==="
```

### Example 2: Conserve Plugin - LIVE Context Analysis

```makefile
# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-bloat: ## Demonstrate bloat scanning (LIVE)
	@echo "=== Conserve Bloat Scan Demo (LIVE) ==="
	@echo ""
	@echo "Scanning this plugin for context bloat..."
	$(UV_RUN) python scripts/bloat_scanner.py --target . --format summary
	@echo ""
	@echo "Use /conserve:bloat-scan for full analysis."

demo-optimize: ## Demonstrate context optimization (LIVE)
	@echo "=== Conserve Optimization Demo (LIVE) ==="
	@echo ""
	@echo "Analyzing context usage in skills/..."
	$(UV_RUN) python scripts/context_analyzer.py --path skills/ --report
	@echo ""
	@echo "Use /conserve:optimize-context for recommendations."

plugin-check: demo-bloat demo-optimize ## Run all live demos
	@echo ""
	@echo "=== Conserve Plugin Check Complete ==="
```

### Example 3: Imbue Plugin - LIVE Review Workflow

```makefile
# ---------- Demo/Dogfood Targets (LIVE) ----------
demo-catchup: ## Demonstrate catchup workflow (LIVE)
	@echo "=== Imbue Catchup Demo (LIVE) ==="
	@echo ""
	@echo "Running catchup on recent git changes..."
	@git log --oneline -5
	@echo ""
	@git diff --stat HEAD~3..HEAD 2>/dev/null || git diff --stat HEAD~1..HEAD
	@echo ""
	@echo "Use /imbue:catchup for full workflow."

demo-review: ## Demonstrate review workflow (LIVE)
	@echo "=== Imbue Review Demo (LIVE) ==="
	@echo ""
	@echo "Running imbue validator on this plugin..."
	$(UV_RUN) python scripts/imbue_validator.py --root . --report
	@echo ""
	@echo "Use /imbue:review for full review workflow."

plugin-check: demo-catchup demo-review ## Run all live demos
	@echo ""
	@echo "=== Imbue Plugin Check Complete ==="
```

### Example 4: Fallback Pattern (No CLI Tools)

For plugins without dedicated CLI tools, demonstrate skill invocation patterns:

```makefile
# ---------- Demo/Dogfood Targets ----------
demo-skills: ## Show available skills and how to invoke them
	@echo "=== $(PLUGIN_NAME) Skills Demo ==="
	@echo ""
	@echo "Available skills (invoke with /$(PLUGIN_NAME):<skill>):"
	@for skill in skills/*/SKILL.md; do \
		name=$$(head -10 "$$skill" | grep '^name:' | cut -d: -f2 | tr -d ' '); \
		desc=$$(head -15 "$$skill" | grep '^description:' | cut -d: -f2- | head -c 50); \
		echo "  /$(PLUGIN_NAME):$$name - $$desc..."; \
	done
	@echo ""
	@echo "Example: /$(PLUGIN_NAME):$$(ls skills/ | head -1)"

plugin-check: demo-skills lint test ## Run demos and quality checks
	@echo ""
	@echo "=== $(PLUGIN_NAME) Plugin Check Complete ==="
```

## Best Practices

### 1. Target Naming

- Use descriptive, hyphenated names
- Group related targets with prefixes (`demo-`, `plugin-`, `quick-`)
- Provide clear `##` comments for auto-documentation

### 2. Error Handling

- Check for required files and directories
- Use `|| true` for non-critical operations
- Provide meaningful error messages

### 3. Output Formatting

- Use consistent section headers (`=== ===`)
- Include status indicators (OK and FAIL/MISSING)
- Provide summary messages

### 4. Customization Points

- Replace hardcoded names with variables
- Make commands configurable with parameters
- Allow for optional features

### 5. Plugin Integration

- Include abstract plugin shared includes
- Follow established conventions
- Support both standalone and aggregated usage

## Usage Examples

### Interactive Generation

```bash
# Generate targets for current plugin
make -f ../abstract/Makefile generate-targets PLUGIN_DIR=$(PWD)

# Generate with custom features
make -f ../abstract/Makefile generate-targets \
  PLUGIN_DIR=$(PWD) \
  FEATURES="feature1,feature2,feature3"

# Generate quick-run targets only
make -f ../abstract/Makefile generate-targets \
  PLUGIN_DIR=$(PWD) \
  TEMPLATE_TYPE=quick-run
```

### Template Customization

```bash
# Extract features from skills for auto-generation
./scripts/extract-features.py skills/ > features.txt

# Generate with extracted features
make -f ../abstract/Makefile generate-targets \
  PLUGIN_DIR=$(PWD) \
  FEATURE_FILE=features.txt
```

This generation module provides detailed templates and workflows for creating contextually appropriate Makefile targets that align with the claude-night-market project's conventions and patterns.
