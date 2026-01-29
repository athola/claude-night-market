---
name: make-dogfood
description: Analyze and enhance Makefiles for complete functionality coverage with auto-generation capability
usage: /make-dogfood [--mode analyze|generate|apply] [--plugin <name>] [--dry-run] [--generate-makefiles] [--preflight-check] [--verbose]
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
- Creating Makefiles for plugins without them

do_not_use_when:
- Writing initial Makefiles from scratch (use --generate-makefiles instead)
- Debugging specific build failures
- Creating custom build systems
</identification>

Use the makefile-dogfooder script to analyze, test, and enhance Makefiles across the claude-night-market project with comprehensive safety checks and auto-generation capabilities.

## Parameters

- `--mode`: Operation mode (default: analyze)
  - `analyze`: Only analyze and report gaps (SAFE - no changes)
  - `generate`: Show generated targets without writing files
  - `apply`: Write targets to Makefiles (use with --dry-run first)

- `--plugin`: Restrict to specific plugin (e.g., `--plugin sanctum`)
  - Recommended: Test on one plugin before applying to all

- `--dry-run`: Preview changes without writing files (HIGHLY RECOMMENDED)
  - Always use this before applying changes for real
  - Shows what will be generated/modified

- `--generate-makefiles`: Generate Makefiles for plugins that don't have them
  - Follows attune:makefile-generation pattern
  - Auto-detects language (Python/Rust/TypeScript)
  - Creates standard targets for detected language

- `--preflight-check`: Run validation checks before processing
  - Validates directories exist
  - Checks write permissions
  - Detects git repository for rollback

- `--verbose`: Show detailed progress and error messages

- `--output`: Output format (text|json, default: text)

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
# SAFE WORKFLOW (Recommended)

# 1. Analyze all plugins to see what's missing
python3 plugins/abstract/scripts/makefile_dogfooder.py --mode analyze

# 2. Generate for a single plugin (see what would be created)
python3 plugins/abstract/scripts/makefile_dogfooder.py --plugin sanctum --mode generate

# 3. Dry-run to preview changes
python3 plugins/abstract/scripts/makefile_dogfooder.py --plugin sanctum --mode apply --dry-run

# 4. Apply for real
python3 plugins/abstract/scripts/makefile_dogfooder.py --plugin sanctum --mode apply

# 5. Generate Makefiles for plugins missing them
python3 plugins/abstract/scripts/makefile_dogfooder.py --generate-makefiles --mode analyze

# 6. Bulk workflow with safety
python3 plugins/abstract/scripts/makefile_dogfooder.py --mode apply --dry-run  # Test all
python3 plugins/abstract/scripts/makefile_dogfooder.py --mode apply  # Apply all
```

## Safety Features

The script includes comprehensive safety checks:

1. **Preflight Validation** (automatic in apply mode)
   - Directory existence checks
   - Write permission verification
   - Git repository detection

2. **Working Directory Validation**
   - Automatic normalization
   - Prevents "file not found" errors

3. **Confirmation Prompt**
   - Prompts before applying without --dry-run
   - Prevents accidental changes

4. **Duplicate Detection**
   - Checks for existing targets
   - Prevents conflicts and warnings

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
