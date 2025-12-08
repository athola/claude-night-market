# Target Generation Module

## Overview

This module provides templates and workflows for generating contextually appropriate Makefile targets for plugins in the claude-night-market project. It supports both aggregator and leaf plugin patterns with customizable templates.

## Template Categories

### 1. Demo Targets

**Purpose:** Demonstrate plugin functionality and showcase key features

#### Basic Demo Template
```makefile
demo: ## Run plugin demonstration
	@echo "=== $(PLUGIN_NAME) Demo ==="
	@echo "Demonstrating core functionality..."
	@echo ""
	@echo "Available skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(basename $$(dirname $$skill)); \
		echo "  - $$name"; \
	done
	@echo ""
	@echo "Demo complete. Use /$(PLUGIN_NAME):skill-name for specific workflows."
```

#### Advanced Demo Template (with feature showcase)
```makefile
demo-features: ## Demonstrate plugin features
	@echo "=== $(PLUGIN_NAME) Feature Demo ==="
	@echo "Plugin capabilities:"
	@echo "  ✓ Feature 1: $(FEATURE_1_DESC)"
	@echo "  ✓ Feature 2: $(FEATURE_2_DESC)"
	@echo "  ✓ Feature 3: $(FEATURE_3_DESC)"
	@echo ""
	@echo "Running feature demonstrations..."
	@echo "Demo complete."
```

### 2. Dogfood Targets

**Purpose:** Test the plugin on itself using its own functionality

#### Self-Validation Template
```makefile
plugin-check: ## Run plugin self-validation
	@echo "=== $(PLUGIN_NAME) Self-Check ==="
	@echo "Validating plugin structure..."
	@echo "Skills: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l)"
	@echo "Tools:  $$(find scripts/ -name '*.py' 2>/dev/null | wc -l)"
	@echo "Tests:  $$(find tests/ -name '*.py' 2>/dev/null | wc -l)"
	@echo ""
	@echo "Checking dependencies..."
	@test -f pyproject.toml && echo "  ✓ pyproject.toml" || echo "  ✗ Missing pyproject.toml"
	@test -f uv.lock && echo "  ✓ uv.lock" || echo "  ✗ Missing uv.lock"
	@echo ""
	@echo "Plugin check complete."
```

#### Self-Test Template
```makefile
plugin-test: ## Test plugin using its own tools
	@echo "=== $(PLUGIN_NAME) Self-Test ==="
	@echo "Testing plugin functionality..."
	@if [ -f scripts/$(PLUGIN_CLI).py ]; then \
		echo "Testing CLI..."; \
		uv run python scripts/$(PLUGIN_CLI).py --test || echo "  CLI test skipped"; \
	fi
	@echo "Self-test complete."
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
	@test -f pyproject.toml || { echo "✗ Missing pyproject.toml"; exit 1; }
	@test -d skills/ || { echo "✗ Missing skills/ directory"; exit 1; }
	@echo "✓ Basic structure valid"
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
	@test -f pyproject.toml && echo "✓ $(PLUGIN_NAME) structure valid"
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
| `PLUGIN_NAME` | Plugin identifier | `conservation` |
| `PLUGIN_DESCRIPTION` | Brief plugin purpose | `Context optimization and resource management` |
| `PLUGIN_CLI` | Main CLI script name | `conservation-cli` |

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

### Example 1: Conservation Plugin (Leaf)

```makefile
# ---------- Demo/Dogfood Targets ----------
demo-context: ## Demo context optimization on own skills
	@echo "=== Conservation Context Demo ==="
	@echo "Demonstrating context-optimization skill..."
	@echo "Skills directory size: $$(du -sh skills/ 2>/dev/null | cut -f1)"
	@echo "Total skill files: $$(find skills/ -name '*.md' 2>/dev/null | wc -l)"

demo-tokens: ## Demo token estimation on own plugin
	@echo "=== Conservation Token Demo ==="
	@echo "Demonstrating token estimation..."
	@total_lines=$$(find skills/ -name "*.md" -exec cat {} \; 2>/dev/null | wc -l); \
	total_tokens=$$((total_lines * 4)); \
	echo "  Total: ~$$total_tokens tokens"

plugin-check: demo-context demo-tokens demo-skills test-skills ## Run all demo workflows
	@echo ""
	@echo "=== Conservation Plugin Check Complete ==="

quick-status: ## Quick project status
	@echo "Conservation: $$(find skills/ -name 'SKILL.md' 2>/dev/null | wc -l) skills, $$(find scripts/ -name '*.py' 2>/dev/null | wc -l) tools"
```

### Example 2: Root Aggregator

```makefile
# ---------- Demo/Dogfood Targets ----------
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

plugin-check: check-all ## Check all plugins
	@echo ""
	@echo "=== All Plugins Check Complete ==="
```

### Example 3: Simple Plugin with Custom Features

```makefile
# ---------- Demo/Dogfood Targets ----------
demo: ## Run plugin demonstration
	@echo "=== MyPlugin Demo ==="
	@echo "Demonstrating core functionality..."
	@echo ""
	@echo "Available skills:"
	@for skill in skills/*/SKILL.md; do \
		name=$$(basename $$(dirname $$skill)); \
		echo "  - $$name"; \
	done

demo-advanced: ## Demonstrate advanced features
	@echo "=== MyPlugin Advanced Demo ==="
	@echo "Advanced capabilities:"
	@echo "  ✓ Batch processing of multiple files"
	@echo "  ✓ Real-time progress monitoring"
	@echo "  ✓ Export to multiple formats"

plugin-check: demo demo-advanced ## Run plugin validation
	@echo ""
	@echo "=== MyPlugin Validation Complete ==="

quick-validate: ## Quick validation check
	@echo "Validating MyPlugin..."
	@test -f pyproject.toml || { echo "✗ Missing pyproject.toml"; exit 1; }
	@test -d skills/ || { echo "✗ Missing skills/ directory"; exit 1; }
	@echo "✓ MyPlugin structure valid"
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
- Include status indicators (`✓` and `✗`)
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

This generation module provides comprehensive templates and workflows for creating contextually appropriate Makefile targets that align with the claude-night-market project's conventions and patterns.