---
name: make-dogfood
description: Analyze and enhance Makefiles for complete functionality coverage
usage: /make-dogfood [--scope root|plugins|all] [--mode analyze|test|full] [--plugin <name>] [--interactive]
---

# Makefile Dogfooding Command

<identification>
triggers: make dogfood, Makefile analysis, Makefile enhancement, missing targets, Makefile gaps, build targets, plugin Makefile, Makefile quality

use_when:
- Analyzing Makefile completeness
- Testing existing make targets
- Generating missing targets
- Preparing plugins for release
- Auditing Makefile coverage across plugins

do_not_use_when:
- Writing initial Makefiles from scratch
- Debugging specific build failures
- Creating custom build systems
</identification>

Use the makefile-dogfooder skill to analyze, test, and enhance Makefiles across the claude-night-market project.

## Parameters

- `--scope`: Target scope (default: all)
  - `root`: Analyze only the root Makefile
  - `plugins`: Analyze plugin Makefiles only
  - `all`: Analyze both root and plugin Makefiles

- `--mode`: Operation mode (default: full)
  - `analyze`: Only analyze and report gaps
  - `test`: Only test existing targets safely
  - `full`: Complete analysis + testing + generation

- `--plugin`: Restrict to specific plugin (e.g., `--plugin abstract`)

- `--interactive`: Prompt before applying changes (default: true for generation)

## Workflow

### 1. Discovery Phase
Scan all Makefiles and build an inventory of existing targets:
- Find all Makefile and .mk files
- Extract target definitions and metadata
- Build dependency graphs
- Identify plugin type (leaf vs aggregator)

### 2. Analysis Phase
Evaluate Makefiles against best practices:
- Check for essential targets (help, clean, test, lint)
- Identify missing convenience targets (demo, quick-run)
- Detect anti-patterns and inconsistencies
- Score each Makefile on completeness (0-100)

### 3. Testing Phase
Safely validate existing targets:
- Run `make -n` for dry-run validation
- Test help targets and documentation coverage
- Verify target dependencies exist
- Check for common runtime issues

### 4. Generation Phase
Create missing targets based on analysis:
- Generate **LIVE demo targets** that run actual CLI tools/scripts
- Add dogfood targets that run plugin tools on the plugin itself
- Create quick-run targets for common workflows
- Ensure demos show REAL output, not static echoes
- Maintain consistency with existing patterns

**Generation Checklist:**
- [ ] Does `demo-*` target run an actual script/tool?
- [ ] Does output show real, dynamic data?
- [ ] Would a user learn something by running this?
- [ ] Is the plugin "eating its own dogfood"?

## Examples

```bash
# Analyze all Makefiles
/make-dogfood --mode analyze

# Test targets only
/make-dogfood --mode test --scope plugins

# Full workflow for single plugin
/make-dogfood --plugin abstract --mode full

# Quick check with auto-apply
/make-dogfood --scope root --mode full --interactive=false
```

## What This Command Does

1. **Creates detailed inventory** of all Makefile targets across the project
2. **Identifies gaps** in user-facing functionality using pattern matching
3. **Tests safely** without modifying files or running risky operations
4. **Generates missing targets** with contextually appropriate templates
5. **Maintains consistency** with existing project patterns and conventions

## CRITICAL: Demo Target Philosophy

**Demo targets must run ACTUAL functionality, not just echo static information.**

| ❌ BAD (Static/Informational) | ✅ GOOD (Live/Functional) |
|-------------------------------|---------------------------|
| `@echo "Skills: 5"` | `$(UV_RUN) python scripts/validator.py --scan` |
| `@find skills/ \| wc -l` | `$(UV_RUN) python scripts/cli.py analyze .` |
| `@echo "Feature: validation"` | `$(UV_RUN) python scripts/validator.py --target .` |

**Reference Pattern** (from ragentop project):
```makefile
demo-detection: build  ## Demonstrate agent session detection (LIVE)
	@echo "=== Agent Session Detection Demo (LIVE) ==="
	@./target/release/ragentop detect --verbose
```

This runs the actual tool and shows REAL output that users would see.

### Good Demo Targets:
- **Run plugin's own CLI tools** on itself (dogfooding)
- **Execute validators/analyzers** on the plugin's own code
- **Show real output** from actual tool invocations
- **Demonstrate user workflows** with live examples

### Bad Demo Targets:
- Echo static feature descriptions
- Count files with `find | wc -l`
- List directory contents
- Print hardcoded capability lists

## Output Format

The command provides:
- Summary report with scores and recommendations
- Detailed findings by Makefile
- Generated targets ready for review
- Integration instructions for applying changes

## Integration with Skills

This command uses the `makefile-dogfooder` skill which provides:
- Modular discovery and analysis components
- Safe testing patterns for validation
- Template-based target generation
- Context-aware recommendations

## See Also

- `/make-dogfood --help` - Show this help
- Plugin-specific help with `make <plugin>-help`
- Root Makefile help with `make help`
