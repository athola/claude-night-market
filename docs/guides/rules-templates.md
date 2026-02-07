# Plugin Rules Templates Guide

Claude Code supports a `.claude/rules/` directory for modular, path-scoped instructions. This guide shows how plugins can provide rule templates that users symlink into their projects.

## Background

From [Claude Code memory documentation](https://code.claude.com/docs/en/memory):

- Rules files are automatically discovered and loaded as project memory
- Supports **path-scoped rules** via YAML frontmatter (`paths: src/**/*.ts`)
- Supports **subdirectory organization** (`frontend/`, `backend/`)
- Supports **symlinks** for sharing rules across projects

## Architecture

```
# User's project
.claude/rules/
├── conserve.md -> ~/.claude-plugins/conserve/rules/conserve.md
├── sanctum.md -> ~/.claude-plugins/sanctum/rules/sanctum.md
└── project-specific.md  # User's own rules

# Plugin distribution
plugins/conserve/rules/
└── conserve.md  # Provided by plugin
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Modular** | Each plugin's context is isolated in its own file |
| **Path-scoped** | Plugin rules can apply only to relevant file types |
| **User-controlled** | Users choose which plugin rules to include |
| **Maintainable** | Plugin updates automatically reflect via symlinks |

## Creating Plugin Rules

### Basic Rule Template

```markdown
---
description: Conservation guidelines for token efficiency
globs: "**/*.py"
alwaysApply: false
---

# Conservation Guidelines

When working with Python files:
- Prefer `Read` with `offset`/`limit` or `Grep` tool over loading whole files
- Use streaming for large file operations
- Monitor context usage with conservation patterns
```

### Frontmatter Options

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief description shown in rule listings |
| `globs` | string/array | File patterns this rule applies to |
| `alwaysApply` | boolean | If true, applies regardless of file context |

### Path-Scoped Examples

**Python-specific rules:**
```markdown
---
globs: "**/*.py"
---

# Python Conservation

- Use `ast` module for code analysis over regex
- Prefer generators for large data processing
- Use `__slots__` for memory-critical classes
```

**Test-specific rules:**
```markdown
---
globs: ["**/test_*.py", "**/tests/**/*.py"]
---

# Test Conservation

- Use pytest fixtures over setUp/tearDown
- Prefer parametrize over duplicate tests
- Use monkeypatch over global mocks
```

## Plugin Rule Templates

### conserve/rules/conserve.md

```markdown
---
description: Token and context conservation patterns
alwaysApply: true
---

# Conservation Principles

## MECW (Maximum Effective Context Window)

Keep context pressure under 50% for quality responses.

## Command Verbosity

| Avoid | Use Instead |
|-------|-------------|
| `npm install` | `npm install --silent` |
| `git log` | `git log --oneline -10` |
| `ls -la` | `ls -1 \| head -20` |

## Discovery Strategy

1. LSP for semantic queries (if enabled)
2. Targeted file reads based on findings
3. `ripgrep` via Grep tool for text search
```

### sanctum/rules/sanctum.md

```markdown
---
description: Git workflow and documentation standards
globs: ["**/*.md", ".git/**"]
---

# Sanctum Conventions

## Commit Messages

- Use conventional commits: `type(scope): description`
- Focus on "why" not "what"
- No AI attribution or emojis

## Documentation

- Progressive disclosure: essential info first
- Audience-appropriate depth
- Link to detailed docs instead of duplicating
```

### parseltongue/rules/parseltongue.md

```markdown
---
description: Python development best practices
globs: "**/*.py"
---

# Python Standards

## Type Hints

- Use `from __future__ import annotations`
- Prefer `T | None` over `Optional[T]`
- Use `TypeVar` for generics

## Testing

- pytest with fixtures
- Coverage target: 85%+
- Integration tests in separate directory
```

## Installation Methods

### Method 1: Manual Symlinks

```bash
# Create rules directory in your project
mkdir -p .claude/rules

# Symlink plugin rules
ln -s ~/.claude-plugins/conserve/rules/conserve.md .claude/rules/
ln -s ~/.claude-plugins/sanctum/rules/sanctum.md .claude/rules/
```

### Method 2: Setup Script

Plugins can provide a setup script:

```bash
#!/bin/bash
# plugins/conserve/scripts/install-rules.sh

PROJECT_DIR="${1:-.}"
RULES_DIR="$PROJECT_DIR/.claude/rules"
PLUGIN_RULES="$(dirname "$0")/../rules"

mkdir -p "$RULES_DIR"

for rule in "$PLUGIN_RULES"/*.md; do
  name=$(basename "$rule")
  if [ ! -e "$RULES_DIR/$name" ]; then
    ln -s "$(realpath "$rule")" "$RULES_DIR/$name"
    echo "Installed: $name"
  else
    echo "Skipped (exists): $name"
  fi
done
```

### Method 3: CLI Command (Future)

```bash
# Proposed: /install-rules command
/install-rules conserve sanctum parseltongue
```

## Rule Conflicts

When multiple plugins provide overlapping rules:

1. **File-specific wins**: Path-scoped rules override general rules
2. **Last loaded wins**: Later rules in alphabetical order take precedence
3. **User rules override**: `project-specific.md` always takes final precedence

### Conflict Resolution Strategy

```markdown
# .claude/rules/00-overrides.md
---
description: Project overrides for plugin rules
alwaysApply: true
---

# Project Overrides

These rules override plugin defaults:

- Prefer verbose git output (disagree with conserve)
- Use 4-space indentation (override parseltongue)
```

## CLAUDE.md vs Rules

| Aspect | CLAUDE.md | .claude/rules/ |
|--------|-----------|----------------|
| Scope | Global project config | Modular, path-scoped |
| Organization | Single file | Multiple files |
| Sharing | Copy/paste | Symlinks |
| Updates | Manual | Automatic via symlinks |
| Path targeting | No | Yes (via frontmatter) |

### Migration Strategy

If you have a large CLAUDE.md, consider splitting:

```bash
# Extract Python rules
grep -A 20 "# Python" CLAUDE.md > .claude/rules/python.md

# Extract Git rules
grep -A 20 "# Git" CLAUDE.md > .claude/rules/git.md

# Keep essentials in CLAUDE.md
# Core identity, project-specific context
```

## Plugin Distribution Checklist

When adding rules to your plugin:

- [ ] Create `rules/` directory in plugin root
- [ ] Add rule files with proper frontmatter
- [ ] Document available rules in README
- [ ] Provide installation script or instructions
- [ ] Test symlink behavior across platforms
- [ ] Consider Windows compatibility (junctions vs symlinks)

## Platform Notes

### macOS/Linux

Symlinks work natively:
```bash
ln -s /path/to/plugin/rules/rule.md .claude/rules/
```

### Windows

Use junctions or enable developer mode for symlinks:
```powershell
# Developer mode enabled
New-Item -ItemType SymbolicLink -Path .claude\rules\rule.md -Target C:\path\to\rule.md

# Without developer mode (junctions for directories)
mklink /J .claude\rules\plugin-rules C:\path\to\plugin\rules
```

## References

- [Claude Code Memory Documentation](https://code.claude.com/docs/en/memory)
- [Claude Code Release Notes (Dec 2025)](https://code.claude.com/releases)
- Issue #56: Original exploration request
