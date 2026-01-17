# Using .claude/rules/ Templates for Plugin Context

Issue #56: Explore .claude/rules/ templates for plugin context injection

## Overview

Claude Code supports a `.claude/rules/` directory for modular, path-scoped instructions. This provides an elegant alternative to CLAUDE.md injection for plugin context.

## How Rules Work

From the [Claude Code memory documentation](https://code.claude.com/docs/en/memory):

- Rules files are automatically discovered and loaded as project memory
- Supports **path-scoped rules** via YAML frontmatter (`paths: src/**/*.ts`)
- Supports **subdirectory organization** (`frontend/`, `backend/`)
- Supports **symlinks** for sharing rules across projects

## Plugin Integration Pattern

Plugins can provide optional `.claude/rules/` templates that users symlink into their projects:

```
# User's project structure
.claude/rules/
├── conservation.md -> ~/.claude-plugins/conservation/rules/conservation.md
├── sanctum.md -> ~/.claude-plugins/sanctum/rules/sanctum.md
└── project-specific.md  # User's own rules
```

### Benefits

1. **Modular**: Each plugin's context is isolated in its own file
2. **Path-scoped**: Plugin rules can apply only to relevant file types
3. **User-controlled**: Users choose which plugin rules to include
4. **Maintainable**: Plugin updates automatically reflect via symlinks

## Example: Conservation Plugin Rules

```markdown
---
paths: "**/*.py"
---

# Conservation Guidelines

When working with Python files:
- Prefer targeted `rg`/`sed -n` slices over reading whole files
- Use streaming for large file operations
- Monitor context usage with conservation patterns
```

## Example: Sanctum Plugin Rules

```markdown
---
paths: "**/*.md"
---

# Sanctum Documentation Rules

When working with documentation:
- Follow directory-specific style rules (docs/ vs book/)
- Check for consolidation opportunities
- Verify accuracy against plugin.json
```

## Setup Instructions

### Manual Symlink

```bash
# Create rules directory if it doesn't exist
mkdir -p .claude/rules/

# Symlink plugin rules
ln -s ~/.claude-plugins/conservation/rules/conservation.md .claude/rules/
ln -s ~/.claude-plugins/sanctum/rules/sanctum.md .claude/rules/
```

### Future: CLI Command

A future `/install-rules` command could automate this:

```bash
# Proposed syntax
/install-rules conservation sanctum

# Would create symlinks automatically
```

## Comparison: CLAUDE.md vs rules/

| Aspect | CLAUDE.md | .claude/rules/ |
|--------|-----------|----------------|
| Location | Single file | Multiple files |
| Scope | Global | Can be path-scoped |
| Organization | Monolithic | Modular |
| Updates | Manual | Automatic (symlinks) |
| User Control | Edit file | Add/remove symlinks |

## Recommendations

1. **Start simple**: Use rules/ for focused, path-scoped guidance
2. **Keep CLAUDE.md**: For project-wide, cross-cutting concerns
3. **Symlink sparingly**: Only include rules you actively need
4. **Document paths**: Make path scoping explicit in frontmatter

## Plugin Authors

If you're creating a plugin that would benefit from rules/:

1. Create a `rules/` directory in your plugin
2. Add focused rule files with path scoping
3. Document symlink setup in your README
4. Keep rules concise (under 100 lines each)

## Current Limitations

- No automatic symlink management
- No conflict detection between plugin rules
- Manual setup required

## See Also

- [Claude Code Memory Documentation](https://code.claude.com/docs/en/memory)
- Plugin-specific setup guides in plugin READMEs
